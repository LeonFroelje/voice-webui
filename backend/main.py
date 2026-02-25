import asyncio
from fastapi import UploadFile, File, Form
import psutil
import time
import datetime
import aiosqlite
from fastapi.responses import StreamingResponse
import json
import os
import uvicorn
from fastapi import FastAPI, WebSocket, WebSocketDisconnect, HTTPException
from fastapi.staticfiles import StaticFiles
import aiomqtt
from pydantic import BaseModel

# Import your settings and the new storage client
from config import settings
from storage import storage_client

DB_PATH = "./data/assistant.db"


# --- DATABASE PRUNER ---
async def db_pruner():
    """Runs periodically to keep the database size in check."""
    while True:
        try:
            async with aiosqlite.connect(DB_PATH) as db:
                # This query deletes everything EXCEPT the 5000 newest records
                await db.execute("""
                    DELETE FROM mqtt_logs 
                    WHERE id NOT IN (
                        SELECT id FROM mqtt_logs ORDER BY id DESC LIMIT 5000
                    )
                """)
                await db.commit()
            print("Vacuumed database: Kept the last 5000 records.")
        except Exception as e:
            print(f"Database pruning error: {e}")

        # Sleep forconds) before running again
        await asyncio.sleep(60 * 60 * 24 * 7)


async def init_db():
    """Creates the database and logs table if they don't exist."""
    # Ensure the data directory exists
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)

    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("""
            CREATE TABLE IF NOT EXISTS mqtt_logs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp TEXT,
                topic TEXT,
                payload TEXT
            )
        """)

        # Optional: Keep the database from growing infinitely
        # Delete logs older than 7 days (or just keep the last X rows)
        await db.commit()


app = FastAPI(title="Voice Assistant WebUI")


class JsonPayload(BaseModel):
    data: dict | list


# --- WEBSOCKET CONNECTION MANAGER ---
class ConnectionManager:
    def __init__(self):
        self.active_connections: list[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)

    def disconnect(self, websocket: WebSocket):
        self.active_connections.remove(websocket)

    async def broadcast(self, message: str):
        for connection in self.active_connections:
            try:
                await connection.send_text(message)
            except Exception:
                pass


manager = ConnectionManager()


async def mqtt_listener():
    """Listens to MQTT, saves to DB, and broadcasts via WebSockets with auto-reconnect."""
    while True:  # <--- Added outer loop to keep it alive forever
        try:
            async with aiomqtt.Client(
                hostname=settings.mqtt_host, port=settings.mqtt_port
            ) as client:
                await client.subscribe("voice/#")
                await client.subscribe("satellites/#")
                await client.subscribe("satellite/#")
                print(
                    "Connected to MQTT Broker. Subscribed to voice/ and satellites/..."
                )

                async for message in client.messages:
                    try:  # <--- Added inner try/except so a bad DB write doesn't drop MQTT
                        payload = message.payload.decode()
                        topic = message.topic.value
                        timestamp = datetime.datetime.now().isoformat()
                        # Save to SQLite
                        async with aiosqlite.connect(DB_PATH) as db:
                            cursor = await db.execute(
                                "INSERT INTO mqtt_logs (timestamp, topic, payload) VALUES (?, ?, ?)",
                                (timestamp, topic, payload),
                            )
                            await db.commit()
                            log_id = cursor.lastrowid

                        # Broadcast to WebSockets
                        time_only = timestamp.split("T")[1][:12]
                        ws_message = json.dumps(
                            {
                                "id": log_id,
                                "time": time_only,
                                "topic": topic,
                                "payload": payload,
                            }
                        )
                        await manager.broadcast(ws_message)

                    except Exception as inner_e:
                        print(f"Error processing message on {topic}: {inner_e}")

        except Exception as e:
            print(f"MQTT Connection lost: {e}. Reconnecting in 5 seconds...")
            await asyncio.sleep(5)  # Wait before trying to reconnect


@app.on_event("startup")
async def startup_event():
    # Initialize the database first
    await init_db()
    asyncio.create_task(db_pruner())
    # Then start the MQTT listener
    asyncio.create_task(mqtt_listener())


# --- SYSTEM ROUTES ---
@app.websocket("/ws/logs")
async def websocket_endpoint(websocket: WebSocket):
    await manager.connect(websocket)
    try:
        while True:
            await websocket.receive_text()
    except WebSocketDisconnect:
        manager.disconnect(websocket)


@app.get("/api/logs/history")
async def get_log_history(limit: int = 200):
    """Fetches the last N logs from the database."""
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        # Order by id DESC to get newest, but limit it
        cursor = await db.execute(
            "SELECT * FROM mqtt_logs ORDER BY id DESC LIMIT ?", (limit,)
        )
        rows = await cursor.fetchall()

        logs = []
        # We reverse the rows so they are in chronological order for the frontend
        for row in reversed(rows):
            # Extract just the time part for the UI display
            time_only = (
                row["timestamp"].split("T")[1][:12]
                if "T" in row["timestamp"]
                else row["timestamp"]
            )

            logs.append(
                {
                    "id": row["id"],
                    "time": time_only,
                    "topic": row["topic"],
                    "payload": row["payload"],
                }
            )

        return {"logs": logs}


@app.get("/api/health")
async def health_check():
    return {
        "status": "ok",
        "mqtt_connected_to": settings.mqtt_host,
        "s3_endpoint": settings.s3_endpoint,
        "s3_bucket": settings.s3_bucket,
    }


# --- S3 STORAGE ROUTES ---
@app.get("/api/s3/files")
async def get_s3_files(prefix: str = ""):
    """Returns a list of all audio files currently in the Garage bucket."""
    files = storage_client.list_files(prefix=prefix)
    return {"files": files}


@app.get("/api/s3/url/{filename:path}")
async def get_file_url(filename: str):
    """
    Generates a presigned URL so the frontend browser can stream
    the audio file directly from the S3/Garage server.
    """
    url = storage_client.get_presigned_url(filename)
    if not url:
        raise HTTPException(status_code=404, detail="Could not generate URL for file")

    return {"filename": filename, "url": url}


# Replace your old /api/s3/url endpoint with this one
@app.get("/api/s3/stream/{filename:path}")
async def stream_audio_file(filename: str):
    """
    Streams the audio file directly through FastAPI to bypass
    browser CORS and Docker network resolution issues.
    """
    stream = storage_client.get_file_stream(filename)
    if not stream:
        raise HTTPException(status_code=404, detail="File not found or unreadable")

    # Return the stream as a wav audio response
    return StreamingResponse(stream, media_type="audio/wav")


def get_s3_object_key(file_id: str) -> str:
    """Maps the URL parameter to the actual S3 object key."""
    if file_id == "tools":
        return "tools.json"
    elif file_id == "vocab":
        return "vocabulary.json"
    elif file_id == "cache":
        return "tool_cache.json"
    else:
        raise HTTPException(status_code=400, detail="Invalid config file ID")


@app.get("/api/config/{file_id}")
async def read_config_file(file_id: str):
    """Reads a JSON configuration file from S3 and returns it."""
    object_key = get_s3_object_key(file_id)

    try:
        content = storage_client.get_json_file(object_key)

        # If the file doesn't exist in the bucket yet, return an empty dict
        if content is None:
            return {"data": {}}

        return {"data": content}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to read from S3: {str(e)}")


@app.post("/api/config/{file_id}")
async def write_config_file(file_id: str, payload: JsonPayload):
    """Writes the updated JSON back to the S3 bucket."""
    object_key = get_s3_object_key(file_id)

    success = storage_client.put_json_file(object_key, payload.data)

    if not success:
        raise HTTPException(status_code=500, detail="Failed to write file to S3")

    return {"status": "success", "message": f"{object_key} saved to S3 successfully"}


# Store the start time for uptime calculation
START_TIME = time.time()

# Mock storage for service heartbeats (MQTT listener updates this)
service_heartbeats = {}


@app.get("/api/system/stats")
async def get_system_stats():
    # Calculate Uptime
    uptime_seconds = int(time.time() - START_TIME)

    # Get RAM/CPU
    cpu_usage = psutil.cpu_percent(interval=None)
    ram = psutil.virtual_memory()

    # Get Disk (Garage S3 storage partition)
    disk = psutil.disk_usage("/")

    return {
        "uptime": uptime_seconds,
        "cpu": cpu_usage,
        "ram_usage": ram.percent,
        "ram_total": round(ram.total / (1024**3), 2),  # GB
        "disk_usage": disk.percent,
        "disk_free": round(disk.free / (1024**3), 2),  # GB
        "services": service_heartbeats,  # { "satellite_kitchen": "2026-02-25T..." }
    }


# --- SPEAKER ENROLLMENT ROUTES ---


@app.post("/api/speaker/upload")
async def upload_speaker_sample(
    speaker_id: str = Form(...), file: UploadFile = File(...)
):
    """Uploads a browser-recorded file to S3 under the speaker's folder."""
    # We'll store samples in a specific 'enrollment' prefix
    object_key = f"enrollment/{speaker_id}/{file.filename}"

    # Read bytes and upload via our storage client
    content = await file.read()
    success = storage_client.s3.put_object(
        Bucket=settings.s3_bucket, Key=object_key, Body=content, ContentType="audio/wav"
    )

    return {"status": "success", "filename": object_key}


@app.post("/api/speaker/enroll")
async def trigger_enrollment(speaker_id: str, filenames: list[str]):
    """Publishes the MQTT message to start the training process."""
    # We use our existing MQTT logic (you'll need to make the client accessible)
    payload = json.dumps({"speaker_id": speaker_id, "filenames": filenames})

    # We can use a temporary client here or share the background one
    async with aiomqtt.Client(hostname=settings.mqtt_host) as client:
        await client.publish("voice/speaker/enroll", payload=payload)

    return {"status": "enrolling", "speaker_id": speaker_id}


frontend_path = os.getenv("FRONTEND_DIST_PATH", "./static/")

app.mount("/", StaticFiles(directory=frontend_path, html=True), name="static")


def main():
    if settings.environment == "PROD":
        uvicorn.run(
            "main:app",
            host=settings.web_host,
            port=settings.web_port,
        )
    else:
        uvicorn.run(
            "main:app", host=settings.web_host, port=settings.web_port, reload=True
        )


if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host=settings.web_host,
        port=settings.web_port,
        reload=True,
    )

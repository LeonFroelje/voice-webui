import argparse
import os
from typing import Optional
from pydantic import SecretStr, Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class WebUISettings(BaseSettings):
    # --- Web Server ---
    web_host: str = Field(
        default="0.0.0.0", description="IP address to bind the FastAPI server to"
    )
    web_port: int = Field(default=8000, description="Port for the FastAPI server")

    # --- MQTT Connection (For Real-time Logs & Metrics) ---
    mqtt_host: str = Field(
        default="localhost", description="Mosquitto broker IP/Hostname"
    )
    mqtt_port: int = Field(default=1883, description="Mosquitto broker port")

    # --- Object Storage (For the S3 Dashboard) ---
    s3_endpoint: str = Field(
        default="http://localhost:3900", description="URL to S3 storage"
    )
    s3_access_key: str = Field(default="your-access-key", description="S3 Access Key")
    s3_secret_key: SecretStr = Field(
        default="your-secret-key", description="S3 Secret Key"
    )
    s3_bucket: str = Field(default="voice-commands", description="S3 Bucket Name")

    # --- System ---
    log_level: str = "INFO"
    environment: str = Field(default="PROD", description="DEV or PROD")

    model_config = SettingsConfigDict(
        env_file=".env", env_file_encoding="utf-8", extra="ignore"
    )


def get_settings() -> WebUISettings:
    parser = argparse.ArgumentParser(description="Voice Assistant WebUI")

    # Web Server
    parser.add_argument("--web-host", help="IP address to bind the web server to")
    parser.add_argument("--web-port", type=int, help="Port for the web server")

    # MQTT
    parser.add_argument("--mqtt-host", help="Mosquitto broker IP/Hostname")
    parser.add_argument("--mqtt-port", type=int, help="Mosquitto broker port")

    # S3
    parser.add_argument("--s3-endpoint", help="URL to S3 storage")
    parser.add_argument("--s3-access-key", help="S3 Access Key")
    parser.add_argument("--s3-secret-key", help="S3 Secret Key")
    parser.add_argument("--s3-bucket", help="S3 Bucket Name")

    # Data Paths
    parser.add_argument("--tools-file-path", help="Path to tools cache JSON")
    parser.add_argument("--vocab-file-path", help="Path to vocabulary JSON")

    # System
    parser.add_argument("--log-level", help="Logging Level (DEBUG, INFO)")

    args, unknown = parser.parse_known_args()
    cli_args = {k.replace("-", "_"): v for k, v in vars(args).items() if v is not None}

    return WebUISettings(**cli_args)


settings = get_settings()

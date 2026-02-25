import boto3
import json
from botocore.exceptions import ClientError
from config import settings
import logging


class StorageClient:
    def __init__(self):
        self.bucket_name = settings.s3_bucket

        # Initialize the boto3 client with our custom endpoint for Garage
        self.s3 = boto3.client(
            "s3",
            endpoint_url=settings.s3_endpoint,
            aws_access_key_id=settings.s3_access_key,
            # Unwrap the Pydantic SecretStr to get the actual string
            aws_secret_access_key=settings.s3_secret_key.get_secret_value(),
            # boto3 usually expects a region even if your local Garage instance ignores it
            region_name="us-east-1",
        )

    def list_files(self, prefix: str = "") -> list[dict]:
        """Lists files in the bucket, optionally filtered by a prefix."""
        try:
            response = self.s3.list_objects_v2(Bucket=self.bucket_name, Prefix=prefix)

            # If the bucket is empty or no files match the prefix
            if "Contents" not in response:
                return []

            files = []
            for obj in response["Contents"]:
                files.append(
                    {
                        "filename": obj["Key"],
                        "size": obj["Size"],  # In bytes
                        "last_modified": obj["LastModified"].isoformat(),
                    }
                )

            # Sort by newest first, which is usually what you want in a dashboard
            files.sort(key=lambda x: x["last_modified"], reverse=True)
            return files

        except ClientError as e:
            logging.error(f"Error listing files from S3: {e}")
            return []

    def download_file(self, object_name: str, destination_path: str) -> bool:
        """Downloads a file from S3 to the local filesystem."""
        try:
            self.s3.download_file(self.bucket_name, object_name, destination_path)
            return True
        except ClientError as e:
            logging.error(f"Error downloading file {object_name}: {e}")
            return False

    def get_presigned_url(self, object_name: str, expiration: int = 3600) -> str | None:
        """
        Generates a temporary, secure URL for the browser to fetch the file directly.
        Expiration is in seconds (default: 1 hour).
        """
        try:
            url = self.s3.generate_presigned_url(
                "get_object",
                Params={"Bucket": self.bucket_name, "Key": object_name},
                ExpiresIn=expiration,
            )
            return url
        except ClientError as e:
            logging.error(f"Error generating presigned URL for {object_name}: {e}")
            return None

    # Add this method to your StorageClient in storage.py
    def get_file_stream(self, object_name: str):
        """Streams the file directly from S3."""
        try:
            response = self.s3.get_object(Bucket=self.bucket_name, Key=object_name)
            return response["Body"]
        except ClientError as e:
            import logging

            logging.error(f"Error streaming file {object_name}: {e}")
            return None

    def get_json_file(self, object_name: str) -> dict | list | None:
        """Reads a JSON file from the S3 bucket and parses it."""
        try:
            response = self.s3.get_object(Bucket=self.bucket_name, Key=object_name)
            # Read the streaming body and decode it
            content = response["Body"].read().decode("utf-8")
            return json.loads(content)
        except ClientError as e:
            # If the file doesn't exist yet, return None so we can handle it
            error_code = e.response.get("Error", {}).get("Code")
            if error_code == "NoSuchKey":
                return None
            logging.error(f"Error reading JSON from {object_name}: {e}")
            raise e
        except json.JSONDecodeError:
            logging.error(f"File {object_name} contains invalid JSON.")
            raise

    def put_json_file(self, object_name: str, data: dict | list) -> bool:
        """Serializes a dictionary/list to JSON and saves it to the S3 bucket."""
        try:
            # Convert python dict/list to a JSON string and encode to bytes
            json_bytes = json.dumps(data, indent=4, ensure_ascii=False).encode("utf-8")

            self.s3.put_object(
                Bucket=self.bucket_name,
                Key=object_name,
                Body=json_bytes,
                ContentType="application/json",  # Good practice to set the MIME type
            )
            return True
        except ClientError as e:
            logging.error(f"Error writing JSON to {object_name}: {e}")
            return False


# Instantiate a single client to be imported and used across your app
storage_client = StorageClient()

import os
import logging
from typing import Optional

logger = logging.getLogger(__name__)

class CloudStorageService:
    def __init__(self):
        self.endpoint = os.getenv("S3_ENDPOINT_URL", "")
        self.bucket = os.getenv("S3_BUCKET_NAME", "wildcard-assets")
        self.enabled = bool(self.endpoint)

    def upload_file(self, local_path: str, destination_key: str) -> Optional[str]:
        if not self.enabled:
            logger.info(f"Cloud storage disabled. Simulated upload for {destination_key}")
            return f"https://mock-cloud.storage/{self.bucket}/{destination_key}"
        try:
            import boto3
            s3 = boto3.client('s3', endpoint_url=self.endpoint)
            s3.upload_file(local_path, self.bucket, destination_key)
            return f"{self.endpoint}/{self.bucket}/{destination_key}"
        except Exception as e:
            logger.error(f"Cloud storage upload error: {e}")
            return None

cloud_storage_service = CloudStorageService()

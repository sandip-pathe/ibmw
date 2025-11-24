"""
Azure Blob Storage service for storing code files and artifacts.
"""
import asyncio
from typing import Optional

from azure.storage.blob.aio import BlobServiceClient
from loguru import logger

from app.config import get_settings
from app.core.exceptions import StorageError

settings = get_settings()


class StorageService:
    """Azure Blob Storage client for file operations."""

    def __init__(self):
        self.enabled = settings.blob_enabled
        self.container_name = settings.blob_container_name
        self.client: Optional[BlobServiceClient] = None

        if self.enabled:
            try:
                self.client = BlobServiceClient.from_connection_string(
                    settings.blob_connection_string
                )
                logger.info("Azure Blob Storage client initialized")
            except Exception as e:
                logger.error(f"Failed to initialize Blob Storage: {e}")
                self.enabled = False

    async def upload_file(
        self, file_path: str, content: bytes, overwrite: bool = True
    ) -> Optional[str]:
        """
        Upload file to blob storage.
        
        Args:
            file_path: Path to store the file (e.g., "repo_id/file.py")
            content: File content as bytes
            overwrite: Whether to overwrite existing file
            
        Returns:
            Blob URL if successful, None otherwise
        """
        if not self.enabled:
            logger.warning("Blob storage is disabled")
            return None

        try:
            blob_client = self.client.get_blob_client(
                container=self.container_name, blob=file_path
            )

            await blob_client.upload_blob(content, overwrite=overwrite)
            logger.info(f"Uploaded file to blob storage: {file_path}")

            return blob_client.url

        except Exception as e:
            logger.error(f"Failed to upload file {file_path}: {e}")
            raise StorageError(f"Failed to upload file: {e}")

    async def download_file(self, file_path: str) -> Optional[bytes]:
        """
        Download file from blob storage.
        
        Args:
            file_path: Path to the file in blob storage
            
        Returns:
            File content as bytes, None if not found
        """
        if not self.enabled:
            logger.warning("Blob storage is disabled")
            return None

        try:
            blob_client = self.client.get_blob_client(
                container=self.container_name, blob=file_path
            )

            download_stream = await blob_client.download_blob()
            content = await download_stream.readall()
            logger.info(f"Downloaded file from blob storage: {file_path}")

            return content

        except Exception as e:
            logger.error(f"Failed to download file {file_path}: {e}")
            return None

    async def delete_file(self, file_path: str) -> bool:
        """
        Delete file from blob storage.
        
        Args:
            file_path: Path to the file in blob storage
            
        Returns:
            True if successful, False otherwise
        """
        if not self.enabled:
            logger.warning("Blob storage is disabled")
            return False

        try:
            blob_client = self.client.get_blob_client(
                container=self.container_name, blob=file_path
            )

            await blob_client.delete_blob()
            logger.info(f"Deleted file from blob storage: {file_path}")
            return True

        except Exception as e:
            logger.error(f"Failed to delete file {file_path}: {e}")
            return False

    async def list_files(self, prefix: str = "") -> list[str]:
        """
        List files in blob storage.
        
        Args:
            prefix: Optional prefix to filter files
            
        Returns:
            List of file paths
        """
        if not self.enabled:
            logger.warning("Blob storage is disabled")
            return []

        try:
            container_client = self.client.get_container_client(self.container_name)
            blobs = []

            async for blob in container_client.list_blobs(name_starts_with=prefix):
                blobs.append(blob.name)

            logger.info(f"Listed {len(blobs)} files with prefix: {prefix}")
            return blobs

        except Exception as e:
            logger.error(f"Failed to list files: {e}")
            return []


# Global storage service instance
storage_service = StorageService()

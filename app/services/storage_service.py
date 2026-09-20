import logging
from typing import Optional
from supabase import create_client, Client
from app.core.config import settings

logger = logging.getLogger(__name__)


class StorageService:
    """
    Service wrapper around Supabase Storage Python SDK.
    Handles signed upload/download URL generation, file liveness checks, file downloads, and file deletion.
    Uses administrative SUPABASE_SERVICE_KEY (backend only).
    """

    _client: Optional[Client] = None

    @classmethod
    def get_client(cls) -> Client:
        """
        Lazily initializes and returns singleton Supabase Client instance.
        """
        if cls._client is None:
            cls._client = create_client(
                settings.SUPABASE_URL,
                settings.SUPABASE_SERVICE_KEY
            )
        return cls._client

    @classmethod
    def create_signed_upload_url(cls, bucket_name: str, storage_path: str) -> str:
        """
        Generates a temporary pre-signed upload URL for direct client file uploads to Supabase Storage.
        
        Returns the signed upload URL string.
        """
        try:
            client = cls.get_client()
            res = client.storage.from_(bucket_name).create_signed_upload_url(storage_path)
            
            # Extract signed_url from dictionary result
            signed_url = res.get("signed_url") or res.get("signedUrl")
            if not signed_url:
                raise ValueError("Supabase SDK returned invalid signed upload URL payload.")
                
            return signed_url
        except Exception as e:
            logger.error(f"Failed to generate signed upload URL for path '{storage_path}': {str(e)}")
            raise e

    @classmethod
    def create_signed_download_url(cls, bucket_name: str, storage_path: str, expires_in: int = 300) -> str:
        """
        Generates a temporary pre-signed download URL for private client file access.
        
        Returns the signed download URL string.
        """
        try:
            client = cls.get_client()
            res = client.storage.from_(bucket_name).create_signed_url(storage_path, expires_in)
            
            # Extract signedURL / signed_url from dictionary result
            signed_url = res.get("signedURL") or res.get("signed_url") or res.get("signedUrl")
            if not signed_url:
                raise ValueError("Supabase SDK returned invalid signed download URL payload.")
                
            return signed_url
        except Exception as e:
            logger.error(f"Failed to generate signed download URL for path '{storage_path}': {str(e)}")
            raise e

    @classmethod
    def download_file(cls, bucket_name: str, storage_path: str) -> bytes:
        """
        Downloads raw file bytes from Supabase Storage for backend OCR processing.
        """
        try:
            client = cls.get_client()
            file_bytes = client.storage.from_(bucket_name).download(storage_path)
            if not file_bytes:
                raise ValueError(f"File at path '{storage_path}' is empty or missing.")
            return file_bytes
        except Exception as e:
            logger.error(f"Failed to download file from path '{storage_path}': {str(e)}")
            raise e

    @classmethod
    def file_exists(cls, bucket_name: str, storage_path: str) -> bool:
        """
        Checks if a file exists in the specified Supabase Storage bucket.
        """
        try:
            client = cls.get_client()
            return client.storage.from_(bucket_name).exists(storage_path)
        except Exception as e:
            logger.error(f"Failed to check file existence for path '{storage_path}': {str(e)}")
            return False

    @classmethod
    def delete_file(cls, bucket_name: str, storage_path: str) -> bool:
        """
        Deletes a file from Supabase Storage bucket.
        """
        try:
            client = cls.get_client()
            client.storage.from_(bucket_name).remove([storage_path])
            return True
        except Exception as e:
            logger.error(f"Failed to delete file at path '{storage_path}': {str(e)}")
            return False

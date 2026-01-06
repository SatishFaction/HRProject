import os
from datetime import datetime, timedelta
from azure.storage.blob import BlobServiceClient, ContentSettings, generate_blob_sas, BlobSasPermissions
from fastapi import HTTPException
from .config import settings

class BlobService:
    def __init__(self):
        self.connection_string = settings.AZURE_STORAGE_CONNECTION_STRING
        self.container_name = settings.AZURE_CONTAINER_NAME
        self.service_client = None
        self.container_client = None
        self.account_name = None
        self.account_key = None

        if self.connection_string:
            try:
                self.service_client = BlobServiceClient.from_connection_string(self.connection_string)
                self.container_client = self.service_client.get_container_client(self.container_name)
                
                # EXTRACT ACCOUNT DETAILS ROBUSTLY
                # 1. Clean the connection string (remove quotes/whitespace)
                cleaned_conn_str = self.connection_string.strip().strip('"').strip("'")
                
                # 2. Parse manually
                parts = {}
                for item in cleaned_conn_str.split(';'):
                    if '=' in item:
                        key, value = item.split('=', 1)
                        parts[key.strip()] = value.strip()
                
                self.account_name = parts.get('AccountName')
                self.account_key = parts.get('AccountKey')

                print(f"DEBUG: Parsed AccountName: '{self.account_name}'")
                if self.account_key:
                     print(f"DEBUG: Parsed AccountKey First 5 chars: {self.account_key[:5]}...")
                     print(f"DEBUG: Parsed AccountKey Length: {len(self.account_key)}")
                else:
                     print("DEBUG: CRITICAL - AccountKey could not be parsed!")

                # Create container if it doesn't exist (Private access by default is safer)
                if not self.container_client.exists():
                     self.container_client.create_container()
            except Exception as e:
                print(f"Failed to initialize Azure Blob Storage: {e}")

    def upload_file(self, file_bytes: bytes, filename: str, content_type: str = "application/pdf") -> str:
        """
        Uploads a file to Azure Blob Storage and returns the filename.
        """
        if not self.service_client:
             raise HTTPException(status_code=500, detail="Azure Storage not configured")

        try:
            blob_client = self.container_client.get_blob_client(filename)
            content_settings = ContentSettings(content_type=content_type)
            blob_client.upload_blob(file_bytes, overwrite=True, content_settings=content_settings)
            
            return filename
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Failed to upload to Azure: {str(e)}")

    def get_sas_url(self, filename: str, expiration_hours: int = 1) -> str:
        """
        Generates a SAS URL for a blob that allows read access for a limited time.
        """
        if not self.service_client or not self.account_key or not self.account_name:
            print("DEBUG: Cannot generate SAS - Missing client, name, or key.")
            return ""

        try:
            sas_token = generate_blob_sas(
                account_name=self.account_name,
                container_name=self.container_name,
                blob_name=filename,
                account_key=self.account_key,
                permission=BlobSasPermissions(read=True),
                expiry=datetime.utcnow() + timedelta(hours=expiration_hours),
                version="2022-11-02"  # Use stable API version
            )
            
            # Construct the full URL
            # Standard Azure Endpoint format: https://<account_name>.blob.core.windows.net/<container_name>/<blob_name>?<sas_token>
            url = f"https://{self.account_name}.blob.core.windows.net/{self.container_name}/{filename}?{sas_token}"
            print(f"DEBUG: Generated SAS URL for {filename}: {url}")
            return url
        except Exception as e:
            print(f"Error generating SAS token: {e}")
            return ""

blob_service = BlobService()

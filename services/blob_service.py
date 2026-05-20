from azure.storage.blob import BlobServiceClient
from services.config import Config
 
class BlobService:
    def __init__(self):
        self.client = BlobServiceClient.from_connection_string(Config.AZURE_STORAGE_CONNECTION_STRING)
        self.container_name = "uploads"
 
    def upload_file(self, file_bytes, blob_name):
        blob_client = self.client.get_blob_client(container=self.container_name, blob=blob_name)
        blob_client.upload_blob(file_bytes, overwrite=True)
        return blob_client.url
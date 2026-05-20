from azure.cosmos import CosmosClient, PartitionKey
from services.config import Config
from datetime import datetime

class DatabaseService:

    def __init__(self):
        self.client = CosmosClient(Config.COSMOS_DB_URL, Config.COSMOS_DB_KEY)
        self.database = self.client.get_database_client(Config.COSMOS_DB_DATABASE)
        self.container = self.database.get_container_client(Config.COSMOS_DB_CONTAINER)

    def store_result(self, blob_name, extracted_text, account_number):
        safe_id = blob_name.replace("/", "_").replace("\\", "_")
        item = {
            "id": safe_id,
            "file_name": blob_name,
            "extracted_text": extracted_text,
            "account_number": account_number,
            "status": "success" if account_number != "No account number found" else "failed",
            "timestamp": datetime.utcnow().isoformat()
        }
        self.container.upsert_item(item)
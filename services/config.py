import os
from dotenv import load_dotenv
 
# Load .env in local dev
load_dotenv()
 
class Config:
    # Blob Storage
    AZURE_STORAGE_CONNECTION_STRING = os.getenv("AZURE_STORAGE_CONNECTION_STRING")
 
    # Document Intelligence
    FORM_RECOGNIZER_ENDPOINT = os.getenv("FORM_RECOGNIZER_ENDPOINT")
    FORM_RECOGNIZER_KEY = os.getenv("FORM_RECOGNIZER_KEY")
 
    # CosmosDB
    COSMOS_DB_URL = os.getenv("COSMOS_DB_URL")
    COSMOS_DB_KEY = os.getenv("COSMOS_DB_KEY")
    COSMOS_DB_DATABASE = os.getenv("COSMOS_DB_DATABASE", "AccountExtractionDB")
    COSMOS_DB_CONTAINER = os.getenv("COSMOS_DB_CONTAINER", "Extractions")
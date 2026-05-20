import sys
import os
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

from fastapi import FastAPI, UploadFile, File
from fastapi.responses import JSONResponse
import logging
import shutil
import tempfile
import threading
import webbrowser
from services.Document_intelligence_service import DocumentIntelligenceService
from services.validator import Validator
from services.database_service import DatabaseService
from dotenv import load_dotenv

load_dotenv()

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="Nigerian Account Number Extractor",
    description="Upload a bank document image and extract the 10-digit NUBAN account number",
    version="1.0.0"
)

@app.get("/")
async def health_check():
    return {"status": "running", "message": "Account Extractor API is live"}

@app.post("/extract-account")
async def extract_account(
    blob_name: str,
    file: UploadFile = File(...)
):
    """
    Upload a bank document image to extract the Nigerian NUBAN account number.
    - **blob_name**: A name to identify this file
    - **file**: The bank document image (JPG, PNG, PDF)
    """
    try:
        logger.info(f"Received file: {blob_name}")

        # Save to temp file
        suffix = os.path.splitext(file.filename)[1]
        with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
            shutil.copyfileobj(file.file, tmp)
            temp_path = tmp.name

        # Extract text lines from image
        doc_service = DocumentIntelligenceService()
        extracted_lines = doc_service.extract_text(temp_path)

        # Extract account number
        validator = Validator()
        account_number = validator.extract_account_number(extracted_lines)

        # Store in CosmosDB
        extracted_text_for_storage = " | ".join(extracted_lines)
        db_service = DatabaseService()
        db_service.store_result(
            blob_name=blob_name,
            extracted_text=extracted_text_for_storage,
            account_number=account_number
        )

        # Clean up temp file
        os.unlink(temp_path)

        logger.info(f"Result: {account_number}")

        return {
            "blob_name": blob_name,
            "account_number": account_number,
            "status": "Success" if account_number != "No account number found" else "Failed",
            "extracted_text_preview": extracted_text_for_storage[:300]
        }

    except Exception as e:
        logger.error(f"Error: {str(e)}", exc_info=True)
        return JSONResponse(
            status_code=500,
            content={"error": str(e)}
        )


if __name__ == "__main__":
    import uvicorn

    def open_browser():
        import time
        time.sleep(1.5)
        webbrowser.open("http://localhost:8001/docs")

    threading.Thread(target=open_browser).start()
    uvicorn.run("api:app", host="0.0.0.0", port=8001, reload=True)
import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))

import logging
import tempfile
import azure.functions as func
from services.Document_intelligence_service import DocumentIntelligenceService
from services.validator import Validator
from services.database_service import DatabaseService


def main(blob: func.InputStream):
    logging.info(f"Processing blob: {blob.name}, size: {blob.length} bytes")

    # Save blob to temp — works on both Windows (local) and Linux (Azure)
    temp_dir = tempfile.gettempdir()
    safe_name = os.path.basename(blob.name)
    temp_file_path = os.path.join(temp_dir, safe_name)

    with open(temp_file_path, "wb") as f:
        f.write(blob.read())

    logging.info(f"Blob saved to temp: {temp_file_path}")

    # Extract text — returns a list of lines
    doc_service = DocumentIntelligenceService()
    extracted_lines = doc_service.extract_text(temp_file_path)

    # Extract account number — validator receives list of lines
    validator = Validator()
    account_number = validator.extract_account_number(extracted_lines)

    # Store result — join lines into string for storage
    extracted_text_for_storage = " | ".join(extracted_lines)

    db_service = DatabaseService()
    db_service.store_result(
        blob_name=blob.name,
        extracted_text=extracted_text_for_storage,
        account_number=account_number
    )

    logging.info(f"Extracted account number: {account_number}")
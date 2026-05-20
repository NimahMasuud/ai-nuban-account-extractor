from azure.ai.documentintelligence import DocumentIntelligenceClient
from azure.ai.documentintelligence.models import AnalyzeDocumentRequest
from azure.core.credentials import AzureKeyCredential
from services.config import Config

class DocumentIntelligenceService:
    def __init__(self):
        self.client = DocumentIntelligenceClient(
            endpoint=Config.FORM_RECOGNIZER_ENDPOINT,
            credential=AzureKeyCredential(Config.FORM_RECOGNIZER_KEY)
        )

    def extract_text(self, file_path):
        with open(file_path, "rb") as f:
            file_bytes = f.read()

        poller = self.client.begin_analyze_document(
            "prebuilt-read",
            AnalyzeDocumentRequest(bytes_source=file_bytes)
        )
        result = poller.result()

        lines = [line.content for page in result.pages for line in page.lines]
        return lines
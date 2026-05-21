# AI NUBAN Account Extractor

A cloud based system that automatically extracts 10-digit Nigerian NUBAN account numbers from bank document images using Azure Document Intelligence for OCR and Python for validation.

---

## What This System Does

Banks and financial institutions in Nigeria process thousands of account opening forms and transfer slips daily all as physical documents or scanned images. Manually reading and entering 10-digit NUBAN account numbers from these images is slow, error-prone, and unscalable.

This system eliminates manual entry entirely. You submit a bank document image and the correct 10-digit account number comes back in under 20 seconds with no human involvement.

---

## The Four Validation Rules

The system is governed by exactly four rules. No exceptions.

- **Rule 1** — Return the first exactly 10-digit sequence found in the image
- **Rule 2** — If no 10-digit sequence exists, return: `No account number found`
- **Rule 3** — Reject any sequence that contains letters, symbols, or spaces
- **Rule 4** — Reject any sequence that is longer or shorter than exactly 10 digits

These four rules working together guarantee zero false positives on every extraction.

---

## Azure Resources Used

| Resource | Name | Purpose |
|---|---|---|
| Resource Group | `account-extraction-rg` | Container for all resources |
| Storage Account | `accountextractionstorage` | Stores uploaded images, triggers the function |
| Blob Container | `uploads` | Where images are uploaded |
| Document Intelligence | `account-extraction-di` | OCR — extracts text from images |
| Function App | `account-extraction-func` | Runs the Python validation logic |
| Cosmos DB | `account-extraction-cosmos` | Stores all extraction results |
| Cosmos DB Database | `AccountExtractionDB` | Database inside Cosmos DB |
| Cosmos DB Container | `Extractions` | Container inside the database |

All resources are deployed in **UK South** region. Cosmos DB is configured as **Serverless** capacity mode.

---

## Project Structure

```
Account_Extraction/
├── function_app/
│   ├── extract_account/
│   │   ├── __init__.py          # Azure Function blob trigger (main processing logic)
│   │   └── function.json        # Blob trigger configuration
│   ├── host.json                # Azure Functions runtime settings
│   ├── local.settings.json      # Local environment config (not committed)
│   └── requirements.txt         # Python dependencies for deployment
├── services/
│   ├── Document_intelligence_service.py  # OCR via Azure Document Intelligence
│   ├── validator.py             # 10-digit account number extraction logic
│   ├── database_service.py      # Cosmos DB storage
│   ├── blob_service.py          # Azure Blob Storage connection
│   └── config.py                # Loads environment variables
├── streamlit_ui/
│   └── app.py                   # Streamlit web interface for manual testing
├── api.py                       # FastAPI interface with Swagger UI
├── .env                         # Secret keys and connection strings (not committed)
├── .gitignore                   # Excludes .env, venv, pycache from Git
└── requirements.txt             # Python dependencies for local development
```

---

## How It Works

The system has two processing modes — automated and manual. Both use the same backend logic.

### Automated Mode — Azure Function (Blob Trigger)

1. An image is uploaded to the `uploads` container in Azure Blob Storage
2. The blob trigger in `function.json` detects the new file instantly
3. Azure calls `__init__.py` automatically — no manual input needed
4. The image is passed to Azure Document Intelligence Read Model
5. Document Intelligence extracts all text as structured lines
6. The validator applies keyword proximity logic and the four rules
7. The result is stored in Cosmos DB with a timestamp and status
8. The whole process completes in under 20 seconds

### Manual Testing Mode — FastAPI

1. Run `python api.py` in the terminal
2. Open `http://localhost:8001/docs` in a browser
3. Use the Swagger UI to upload an image and enter a blob name
4. Click Execute to see the extracted account number in the JSON response
5. The result is also stored in Cosmos DB

### Manual Testing Mode — Streamlit

1. Run `streamlit run streamlit_ui/app.py --server.port 8502`
2. Open `http://localhost:8502` in a browser
3. Upload a bank image and enter a file label
4. Click Extract Account Number to see the result on screen

---

## What Each File Does

**`function_app/extract_account/__init__.py`**
This is the Azure Function. It runs automatically when a file is uploaded to the `uploads` container. It saves the blob to a temp file, calls Document Intelligence for OCR, passes the result to the validator, and stores the final result in Cosmos DB.

**`function_app/extract_account/function.json`**
This defines the blob trigger. It tells Azure to watch the `uploads` container and call the function automatically when a new file arrives.

**`services/Document_intelligence_service.py`**
This connects to Azure Document Intelligence using the prebuilt Read model. Its only job is to receive an image file, send it to Microsoft's OCR engine, and return a list of text lines. It does not apply any business rules.

**`services/validator.py`**
This contains the 10-digit extraction logic. It receives the list of lines from Document Intelligence and applies two steps — first it searches near account-related keywords like "Account No", "NUBAN", and "Acct". If a valid 10-digit number is found near a keyword, it is returned immediately. If not, it scans every line for the first valid match. If nothing is found, it returns `No account number found`.

**`services/database_service.py`**
This connects to Azure Cosmos DB. It stores every extraction result permanently — the file name, extracted text, account number, status (success or failed), and a timestamp.

**`services/blob_service.py`**
This manages the connection to Azure Blob Storage. It handles uploading files to the `uploads` container.

**`services/config.py`**
This loads all environment variables from the `.env` file. Every other service reads its credentials from here.

**`api.py`**
This is the FastAPI application. It creates a Swagger UI at `localhost:8001/docs` where developers can upload an image and immediately see the extracted account number. It uses the same services as the Azure Function.

**`streamlit_ui/app.py`**
This is the Streamlit interface. It provides a cleaner visual UI for manual testing at `localhost:8502`. It uses the same services as the FastAPI and Azure Function.

---

## Validation Logic in Detail

The validator (`validator.py`) works in two steps:

**Step 1 — Keyword Proximity Search**

The validator searches every line for account-related keywords:
```
account, acct, acc no, account no, nuban, acct no, account number
```
If a line contains any of these keywords, it searches that line for a valid 10-digit number first. This solves the two-10-digit problem — a bank slip that contains both an account number and a transaction reference will return the account number because the keyword is near it.

**Step 2 — Full Document Scan (Fallback)**

If no keyword match is found, the validator scans every line in the document and returns the first valid 10-digit sequence it finds.

**OCR Noise Cleaning**

Before checking length, the validator strips internal spaces and dashes from number sequences using `re.sub(r'[\s\-]', '', candidate)`. This handles cases where OCR inserts a space inside a number — for example `12345 67890` is cleaned to `1234567890` before validation.

---

## Why Azure Document Intelligence (Not Azure AI Vision)

Microsoft explicitly recommends Document Intelligence for financial documents. Three specific reasons apply to this project:

1. **Higher resolution OCR** — Document Intelligence runs at greater resolution than Vision, directly improving accuracy on small printed digits
2. **Line level structured output** — results are returned as pages, lines, and words with positional coordinates. This prevents a 10-digit account number from being split across two OCR tokens
3. **Prebuilt bank statement model excluded** — the `prebuilt-bankStatement.us` model was evaluated and rejected because it is locked to US bank formats (routing numbers, IBAN, SWIFT) and is incompatible with the Nigerian NUBAN 10-digit structure

---

## Why Python Over Power Automate

Power Automate was evaluated and rejected for three technical reasons:

1. **OCR noise handling** — real bank image scans can produce `012 345 6789` instead of `0123456789` due to scan gaps. Python removes this noise with `re.sub()` before applying the regex. Power Automate cannot pre-process raw OCR strings this way
2. **Two 10-digit problem** — a bank slip may contain both a 10-digit account number and a 10-digit transaction reference. Python applies keyword proximity logic to search near `Account No` labels first. Power Automate cannot implement this logic without significant workarounds
3. **Deployment flexibility** — the Azure Function exposes a single HTTP endpoint callable from any future system — mobile apps, web applications, Power Apps — without rebuilding the logic

---

## Local Setup

### Prerequisites

- Python 3.12
- Azure CLI installed and logged in
- Azure Functions Core Tools v4
- An active Azure subscription with the resources listed above created

### Steps

**1. Clone the repository**
```powershell
git clone https://github.com/YOUR_USERNAME/ai-nuban-account-extractor.git
cd ai-nuban-account-extractor
```

**2. Create and activate virtual environment**
```powershell
python -m venv venv
.\venv\Scripts\Activate.ps1
```

**3. Install dependencies**
```powershell
pip install -r requirements.txt
```

**4. Create your `.env` file**

Create a file named `.env` in the root of the project and fill in your Azure credentials:
```
AZURE_STORAGE_CONNECTION_STRING=your_storage_connection_string
FORM_RECOGNIZER_ENDPOINT=https://your-resource.cognitiveservices.azure.com/
FORM_RECOGNIZER_KEY=your_document_intelligence_key
COSMOS_DB_URL=https://your-cosmos.documents.azure.com:443/
COSMOS_DB_KEY=your_cosmos_primary_key
COSMOS_DB_DATABASE=AccountExtractionDB
COSMOS_DB_CONTAINER=Extractions
```

**5. Run the Azure Function locally**
```powershell
cd function_app
func start
```

**6. Run the FastAPI interface**
```powershell
python api.py
```
Then open `http://localhost:8001/docs`

**7. Run the Streamlit interface**
```powershell
streamlit run streamlit_ui/app.py --server.port 8502
```
Then open `http://localhost:8502`

---

## Deploying to Azure

**1. Log in to Azure CLI**
```powershell
az login --use-device-code
```

**2. Copy requirements.txt to function_app folder**
```powershell
copy requirements.txt function_app\requirements.txt
```

**3. Deploy**
```powershell
cd function_app
func azure functionapp publish account-extraction-func
```

**4. Add environment variables in Azure Portal**

Go to Azure Portal → `account-extraction-func` → Settings → Environment variables → App settings

Add all 7 variables from your `.env` file one by one, then click Apply and Confirm.

---

## Testing

The system was tested against 8 real Nigerian bank account opening forms:

| File | Account Number | Status |
|---|---|---|
| Image1.jpeg | 1004455662 | ✅ Success |
| Image6.jpeg | 2250207262 | ✅ Success |
| Image8.jpeg | 3116425210 | ✅ Success |
| Image9.jpeg | 1212020567 | ✅ Success |
| Image17.jpeg | 2024202302 | ✅ Success |
| Image18.jpeg | 0404200401 | ✅ Success |
| Image14.jpeg | No account number found | ❌ Not found |
| Image3.jpeg | No account number found | ❌ Not found |

### Edge Case Tests

| Test | Input | Expected Result | Actual Result |
|---|---|---|---|
| Phone number only | Image with 08012345678 | No account number found | ✅ Passed |
| Two 10-digit numbers | Account No + Transaction Ref | Account number (keyword hit) | ✅ Passed |
| OCR space in number | 12345 67890 | 1234567890 | ✅ Passed |
| Blurry image | Low quality scan | Extracted or not found | ✅ Passed |

---

## Cosmos DB Record Structure

Every extraction is stored in Cosmos DB with this structure:

```json
{
  "id": "uploads_Image1.jpeg",
  "file_name": "uploads/Image1.jpeg",
  "extracted_text": "INDIVIDUAL ACCOUNT OPENING FORM | ...",
  "account_number": "1004455662",
  "status": "success",
  "timestamp": "2026-04-02T12:27:42.578618"
}
```

---

## Supported File Types

Azure Document Intelligence Read Model supports:
- JPEG / JPG
- PNG
- PDF
- TIFF
- BMP

---

## Security Notes

- The `.env` file is excluded from Git via `.gitignore`  never commit it
- The `uploads` container in Blob Storage is set to **Private**  anonymous access is disabled
- All Azure resources are authenticated via connection strings and API keys stored in environment variables
- For production deployment, replace API key authentication with Azure Entra ID (formerly Azure Active Directory)

---

## Author

Nimatallahi Masuud

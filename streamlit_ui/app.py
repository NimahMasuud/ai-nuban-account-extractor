import streamlit as st
import sys
import os
import tempfile

# Add project root to path so services can be imported
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from services.Document_intelligence_service import DocumentIntelligenceService
from services.validator import Validator
from services.database_service import DatabaseService

# ─── Page Config ──────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="Nigerian Account Number Extractor",
    page_icon="🏦",
    layout="centered"
)

# ─── Custom Styling ───────────────────────────────────────────────────────────
st.markdown("""
<style>
    .main-header {
        background: linear-gradient(90deg, #1A1A1A, #2A2A2A);
        padding: 20px;
        border-radius: 10px;
        border-left: 5px solid #E8A020;
        margin-bottom: 20px;
    }
    .result-success {
        background-color: #d4edda;
        border: 2px solid #28a745;
        border-radius: 8px;
        padding: 15px;
        text-align: center;
    }
    .result-failed {
        background-color: #f8d7da;
        border: 2px solid #dc3545;
        border-radius: 8px;
        padding: 15px;
        text-align: center;
    }
    .account-number {
        font-size: 36px;
        font-weight: bold;
        color: #065A82;
    }
    .info-box {
        background-color: #f8f9fa;
        border-left: 4px solid #E8A020;
        padding: 12px;
        border-radius: 4px;
        margin: 10px 0;
    }
</style>
""", unsafe_allow_html=True)

# ─── Header ───────────────────────────────────────────────────────────────────
st.markdown("""
<div class="main-header">
    <h1 style="color: white; margin: 0;">🏦 Nigerian Account Number Extractor</h1>
    <p style="color: #E8A020; margin: 5px 0 0 0;">Powered by Azure Document Intelligence + Python</p>
</div>
""", unsafe_allow_html=True)

# ─── Sidebar ──────────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("### ℹ️ How It Works")
    st.markdown("""
    1. **Upload** a bank document image
    2. **Azure OCR** extracts all text
    3. **Validator** finds the 10-digit NUBAN
    4. **Result** saved to Cosmos DB
    """)
    st.divider()
    st.markdown("### 📋 Supported Formats")
    st.markdown("- JPEG / JPG\n- PNG\n- PDF\n- TIFF\n- BMP")
    st.divider()
    st.markdown("### ⚙️ Validation Rules")
    st.markdown("""
    - ✅ Exactly 10 digits
    - ✅ No letters or symbols
    - ✅ Keyword proximity first
    - ✅ OCR noise cleaning
    """)

# ─── Main Upload Area ─────────────────────────────────────────────────────────
st.markdown("### 📤 Upload Bank Document")

col1, col2 = st.columns([2, 1])

with col1:
    uploaded_file = st.file_uploader(
        "Choose a bank image or document",
        type=["jpg", "jpeg", "png", "pdf", "tiff", "bmp"],
        help="Upload any Nigerian bank document containing an account number"
    )

with col2:
    blob_name = st.text_input(
        "File Label",
        placeholder="e.g. Image_1",
        help="A name to identify this file in the database"
    )

# ─── Process Button ───────────────────────────────────────────────────────────
if uploaded_file and blob_name:
    if st.button("🔍 Extract Account Number", use_container_width=True, type="primary"):

        with st.spinner("Processing document..."):

            suffix = os.path.splitext(uploaded_file.name)[1]
            with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
                tmp.write(uploaded_file.read())
                temp_path = tmp.name

            try:
                with st.status("Running Azure Document Intelligence OCR...") as status:
                    doc_service = DocumentIntelligenceService()
                    extracted_lines = doc_service.extract_text(temp_path)
                    status.update(label="✅ OCR Complete", state="complete")

                with st.status("Applying validation logic...") as status:
                    validator = Validator()
                    account_number = validator.extract_account_number(extracted_lines)
                    status.update(label="✅ Validation Complete", state="complete")

                with st.status("Saving to Cosmos DB...") as status:
                    extracted_text = " | ".join(extracted_lines)
                    db_service = DatabaseService()
                    db_service.store_result(
                        blob_name=blob_name,
                        extracted_text=extracted_text,
                        account_number=account_number
                    )
                    status.update(label="✅ Saved to Cosmos DB", state="complete")

                os.unlink(temp_path)

                st.divider()

                is_success = account_number != "No account number found"

                if is_success:
                    st.markdown(f"""
                    <div class="result-success">
                        <p style="margin:0; color:#155724; font-size:14px;">✅ ACCOUNT NUMBER FOUND</p>
                        <p class="account-number">{account_number}</p>
                        <p style="margin:0; color:#155724; font-size:12px;">Status: SUCCESS — Saved to Cosmos DB</p>
                    </div>
                    """, unsafe_allow_html=True)
                else:
                    st.markdown(f"""
                    <div class="result-failed">
                        <p style="margin:0; color:#721c24; font-size:14px;">❌ NO ACCOUNT NUMBER FOUND</p>
                        <p style="font-size:20px; font-weight:bold; color:#721c24;">No account number found</p>
                        <p style="margin:0; color:#721c24; font-size:12px;">Status: FAILED — Result saved to Cosmos DB</p>
                    </div>
                    """, unsafe_allow_html=True)

                st.divider()

                with st.expander("📄 View Extracted Text"):
                    st.markdown(f"""
                    <div class="info-box">
                        <strong>Raw OCR Output:</strong><br>
                        <small style="color: #555;">{extracted_text[:500]}{'...' if len(extracted_text) > 500 else ''}</small>
                    </div>
                    """, unsafe_allow_html=True)

                if uploaded_file.type.startswith("image"):
                    with st.expander("🖼️ View Uploaded Document"):
                        st.image(uploaded_file, caption=uploaded_file.name, use_column_width=True)

            except Exception as e:
                st.error(f"❌ Error processing document: {str(e)}")
                if os.path.exists(temp_path):
                    os.unlink(temp_path)

elif uploaded_file and not blob_name:
    st.warning("⚠️ Please enter a File Label before extracting.")

elif not uploaded_file:
    st.markdown("""
    <div class="info-box">
        <strong>👆 Upload a bank document above to get started.</strong><br>
        <small>The system will automatically extract the 10-digit Nigerian NUBAN account number.</small>
    </div>
    """, unsafe_allow_html=True)

# ─── Footer ───────────────────────────────────────────────────────────────────
st.divider()
st.markdown("""
<p style="text-align:center; color:#888; font-size:12px;">
    Built with Azure Document Intelligence · Azure Functions · Cosmos DB · Streamlit<br>
    <strong>INFINION</strong> — Nigerian Account Number Extraction System
</p>
""", unsafe_allow_html=True)
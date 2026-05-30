from fastapi import FastAPI, HTTPException, UploadFile, File
from decimal import Decimal
import uuid
import os
import shutil
import base64

from lib.api_models import InvoiceRequest, ISAIRequest
from lib.fiscal_engine import sanitize_name, calculate_isai_manzanillo, calculate_retentions, validate_postal_code
from lib.xml_generator import generate_signed_xml
from lib.ocr_engine import extract_text_from_pdf, extract_structured_data

app = FastAPI(title="Notaria 4 Digital Core API", version="1.0.0")

@app.get("/health")
def health_check():
    return {"status": "ok", "service": "notaria-4-core-backend"}

@app.post("/api/v1/cfdi")
def create_cfdi(request: InvoiceRequest):
    # Pydantic v2 compatibility
    data = request.model_dump()

    # 1. Sanitize Receptor Name
    data['receptor']['nombre'] = sanitize_name(data['receptor']['nombre'])

    # 1.1 Validate Postal Code
    # Assuming the API receives the 'domicilio_fiscal' as the CP code
    if not validate_postal_code(data['receptor']['domicilio_fiscal']):
         raise HTTPException(status_code=400, detail=f"Invalid Postal Code: {data['receptor']['domicilio_fiscal']}")

    # 2. Calculate Retentions (Logic Check)
    retentions = calculate_retentions(
        data['receptor']['rfc'],
        data['subtotal']
    )

    # 3. Generate XML
    try:
        xml_bytes = generate_signed_xml(data)
        # In a real scenario, we might upload this to storage and return a URL
        # For now, return the stub content
        return {
            "status": "success",
            "xml_base64": base64.b64encode(xml_bytes).decode('utf-8'), # Encode base64
            "retentions_calculated": retentions
        }
    except ValueError as ve:
        raise HTTPException(status_code=400, detail=f"Validation Error: {str(ve)}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/v1/calculate-isai")
def calculate_isai(request: ISAIRequest):
    isai = calculate_isai_manzanillo(request.operation_price, request.cadastral_value)
    return {"isai": isai}

@app.post("/api/v1/extract-data")
def extract_data(file: UploadFile = File(...)):
    if not file.filename.endswith('.pdf'):
        raise HTTPException(status_code=400, detail="Only PDF files are supported.")

    # Secure temporary file saving
    temp_dir = "/tmp/notaria4_uploads"
    os.makedirs(temp_dir, exist_ok=True)

    safe_filename = f"{uuid.uuid4().hex}.pdf"
    temp_path = os.path.join(temp_dir, safe_filename)

    try:
        with open(temp_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)

        with open(temp_path, "rb") as f:
            pdf_bytes = f.read()

        text = extract_text_from_pdf(pdf_bytes)
        structured_data = extract_structured_data(text)

        return {
            "status": "success",
            "extracted_data": structured_data
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        if os.path.exists(temp_path):
            os.remove(temp_path)

@app.get("/")
def root():
    return {"message": "Notaria 4 Digital Core API"}

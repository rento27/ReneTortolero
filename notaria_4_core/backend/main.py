from fastapi import FastAPI, HTTPException, UploadFile, File
from decimal import Decimal
import uuid
import os
import shutil

from lib.api_models import InvoiceRequest, ISAIRequest, InvoiceResponse
from lib.fiscal_engine import sanitize_name, calculate_isai_manzanillo, calculate_retentions, validate_postal_code, validate_conceptos_objeto_imp
from lib.xml_generator import generate_signed_xml
from lib.ocr_engine import extract_text_from_pdf, extract_structured_data
from lib.pdf_generator import generate_hybrid_pdf

app = FastAPI(title="Notaria 4 Digital Core API", version="1.0.0")

@app.get("/health")
def health_check():
    return {"status": "ok", "service": "notaria-4-core-backend"}

@app.post("/api/v1/cfdi", response_model=InvoiceResponse)
def create_cfdi(request: InvoiceRequest):
    # Pydantic v2 compatibility
    data = request.model_dump()

    try:
        # 0. Validate ObjetoImp
        validate_conceptos_objeto_imp(data['conceptos'])

        # 1. Sanitize Receptor Name
        data['receptor']['nombre'] = sanitize_name(data['receptor']['nombre'])

        # 1.1 Validate Postal Code
        if not validate_postal_code(data['receptor']['domicilio_fiscal']):
             raise HTTPException(status_code=400, detail=f"Invalid Postal Code: {data['receptor']['domicilio_fiscal']}")

        # 2. Calculate Retentions (Logic Check)
        retentions = calculate_retentions(
            data['receptor']['rfc'],
            data['subtotal']
        )

        # 3. Generate XML
        import base64
        xml_bytes = generate_signed_xml(data)

        # 4. Generate Hybrid PDF
        pdf_bytes = generate_hybrid_pdf(xml_bytes, data)
        pdf_base64 = base64.b64encode(pdf_bytes).decode('utf-8') if pdf_bytes else None

        # Return the response
        return InvoiceResponse(
            status="success",
            xml_base64=base64.b64encode(xml_bytes).decode('utf-8'),
            retentions_calculated=retentions,
            pdf_base64=pdf_base64
        )
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

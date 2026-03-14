from fastapi import FastAPI, HTTPException, UploadFile, File
from lib.api_models import InvoiceRequest, ISAIRequest
from typing import Optional
from lib.fiscal_engine import sanitize_name, calculate_isai_manzanillo, calculate_retentions, validate_postal_code
from lib.xml_generator import generate_signed_xml
from lib.ocr_engine import extract_text_hybrid, process_text_nlp
from decimal import Decimal

app = FastAPI(title="Notaria 4 Digital Core API", version="1.0.0")

@app.get("/health")
def health_check():
    return {"status": "ok", "service": "notaria-4-core-backend"}

@app.post("/api/v1/cfdi")
def create_cfdi(request: InvoiceRequest):
    data = request.model_dump()

    # 1. Sanitize Receptor Name
    data['receptor']['nombre'] = sanitize_name(data['receptor']['nombre'])

    # 1.1 Validate Postal Code
    if not validate_postal_code(data['receptor']['domicilio_fiscal']):
         raise HTTPException(status_code=400, detail=f"Invalid Postal Code: {data['receptor']['domicilio_fiscal']}")

    # 2. Generate XML
    try:
        xml_bytes = generate_signed_xml(data)
        return {
            "status": "success",
            "xml_base64": xml_bytes.decode('utf-8')
        }
    except ValueError as ve:
        raise HTTPException(status_code=400, detail=f"Validation Error: {str(ve)}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/v1/calculate-isai")
def calculate_isai(request: ISAIRequest):
    try:
        isai_amount = calculate_isai_manzanillo(request.operation_price, request.cadastral_value)
        return {
            "operation_price": request.operation_price,
            "cadastral_value": request.cadastral_value,
            "isai_calculated": isai_amount
        }
    except Exception as e:
         raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/v1/extract-data")
async def extract_data(file: UploadFile = File(...)):
    try:
        contents = await file.read()
        text = extract_text_hybrid(contents)
        if not text:
            return {"status": "error", "message": "Failed to extract text from PDF."}

        entities = process_text_nlp(text)

        return {
            "status": "success",
            "text_length": len(text),
            "entities": entities
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/")
def root():
    return {"message": "Notaria 4 Digital Core API"}

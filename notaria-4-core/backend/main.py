from fastapi import FastAPI, UploadFile, File, HTTPException
from pydantic import BaseModel
from typing import List
from decimal import Decimal

# Import our custom engines
from lib.fiscal_engine import sanitize_name, calculate_retentions, calculate_isai_manzanillo
from lib.extraction_engine import ExtractionEngine

app = FastAPI(title="Notaría 4 Digital Core API", version="1.0.0")

# Initialize engines
extractor = ExtractionEngine()

class FiscalRequest(BaseModel):
    rfc_receptor: str
    nombre_receptor: str
    subtotal: Decimal
    iva_trasladado: Decimal

class FiscalResponse(BaseModel):
    sanitized_name: str
    retentions: dict

class IsaiRequest(BaseModel):
    precio_operacion: Decimal
    valor_catastral: Decimal
    tasa: Decimal = Decimal("0.03") # Default 3%

@app.get("/")
def read_root():
    return {"status": "active", "service": "Notaría 4 Digital Core"}

@app.post("/fiscal/validate", response_model=FiscalResponse)
def validate_fiscal_data(request: FiscalRequest):
    """
    Validates fiscal data rules:
    - Name sanitization
    - Persona Moral retentions
    """
    clean_name = sanitize_name(request.nombre_receptor)
    retentions = calculate_retentions(request.rfc_receptor, request.subtotal, request.iva_trasladado)

    return {
        "sanitized_name": clean_name,
        "retentions": retentions
    }

@app.post("/fiscal/calculate-isai")
def calculate_isai(request: IsaiRequest):
    """
    Calculates ISAI Manzanillo
    """
    impuesto = calculate_isai_manzanillo(request.precio_operacion, request.valor_catastral, request.tasa)
    return {"isai_amount": impuesto}

@app.post("/extraction/process-deed")
async def process_deed(file: UploadFile = File(...)):
    """
    Upload a PDF deed to extract text and entities.
    """
    if file.content_type != "application/pdf":
        raise HTTPException(status_code=400, detail="File must be a PDF")

    content = await file.read()

    # 1. Extract Text
    text = extractor.extract_text_from_pdf(content)

    # 2. Extract Entities
    entities = extractor.extract_entities(text)

    return {
        "filename": file.filename,
        "extracted_entities": entities,
        "text_preview": text[:500] + "..." # Preview first 500 chars
    }

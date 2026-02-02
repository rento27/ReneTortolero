import os
from fastapi import FastAPI, UploadFile, File, HTTPException
from pydantic import BaseModel
from typing import List
from decimal import Decimal
from lib.fiscal_engine import FiscalEngine
from lib.extraction_engine import ExtractionEngine

app = FastAPI(title="Notaría 4 Digital Core API")

class FiscalCalculationRequest(BaseModel):
    rfc_receptor: str
    subtotal: float
    is_persona_moral: bool

class IsaiRequest(BaseModel):
    price: float
    cadastral_value: float

@app.get("/")
def health_check():
    return {"status": "operational", "system": "Notaría 4 Digital Core"}

@app.post("/calculate-fiscal")
def calculate_fiscal(request: FiscalCalculationRequest):
    """
    Calculates taxes including logic for Persona Moral retentions.
    """
    subtotal = Decimal(str(request.subtotal))

    # Base IVA (16%)
    iva = subtotal * Decimal('0.16')

    retentions = {"isr_retention": Decimal(0), "iva_retention": Decimal(0)}

    # Force check logic based on RFC length as per architecture,
    # but allow explicit override flag for testing.
    if len(request.rfc_receptor) == 12 or request.is_persona_moral:
        retentions = FiscalEngine.calculate_retentions_persona_moral(subtotal)

    return {
        "subtotal": float(subtotal),
        "iva_trasladado": float(iva),
        "retenciones": {k: float(v) for k, v in retentions.items()},
        "total": float(subtotal + iva - retentions['isr_retention'] - retentions['iva_retention'])
    }

@app.post("/isai-calc")
def calculate_isai_endpoint(request: IsaiRequest):
    """
    Calculates ISAI based on Manzanillo rules.
    """
    # In production, fetch rate from Firebase Remote Config
    rate = Decimal('0.03')

    isai = FiscalEngine.calculate_isai_manzanillo(
        Decimal(str(request.price)),
        Decimal(str(request.cadastral_value)),
        rate
    )
    return {"isai_amount": float(isai), "rate_applied": float(rate)}

@app.post("/sanitize-name")
def sanitize_name_endpoint(name: str):
    return {"original": name, "sanitized": FiscalEngine.sanitize_name(name)}

@app.post("/extract-text")
async def extract_text_endpoint(file: UploadFile = File(...)):
    if not file.filename.endswith(".pdf"):
        raise HTTPException(status_code=400, detail="Only PDFs are supported")

    contents = await file.read()
    text = ExtractionEngine.extract_text_smart(contents)

    return {"filename": file.filename, "extracted_text_preview": text[:500], "full_length": len(text)}

@app.get("/xml/preview")
def preview_xml_structure():
    """
    Stub to demonstrate where satcfdi logic resides.
    """
    return {"status": "Not implemented. Requires valid CSD credentials from Secret Manager."}

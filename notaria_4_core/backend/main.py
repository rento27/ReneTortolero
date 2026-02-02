import os
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from decimal import Decimal
from typing import List, Optional

from lib.fiscal_engine import sanitize_name, calculate_retentions, validate_copropiedad, calculate_isai
from lib.extraction_engine import ExtractionEngine

app = FastAPI(title="Notaría 4 Digital Core API")

extraction_engine = ExtractionEngine()

class FiscalRequest(BaseModel):
    rfc_receptor: str
    nombre_receptor: str
    subtotal: Decimal

class ISAIRequest(BaseModel):
    precio_operacion: Decimal
    valor_catastral: Decimal
    tasa: Decimal # Should come from Remote Config, but passed here for calculation

class CopropiedadRequest(BaseModel):
    porcentajes: List[Decimal]

@app.get("/")
def health_check():
    return {"status": "ok", "service": "Notaría 4 Core"}

@app.post("/calculate-fiscal")
def calculate_fiscal_data(req: FiscalRequest):
    """
    Calculates retentions and sanitizes name.
    """
    sanitized_name = sanitize_name(req.nombre_receptor)
    retentions = calculate_retentions(req.rfc_receptor, req.subtotal)

    return {
        "sanitized_name": sanitized_name,
        "retentions": retentions
    }

@app.post("/calculate-isai")
def calculate_isai_endpoint(req: ISAIRequest):
    isai = calculate_isai(req.precio_operacion, req.valor_catastral, req.tasa)
    return {"isai_amount": isai}

@app.post("/validate-copropiedad")
def validate_copropiedad_endpoint(req: CopropiedadRequest):
    is_valid = validate_copropiedad(req.porcentajes)
    if not is_valid:
        raise HTTPException(status_code=400, detail="Percentages do not sum to exactly 100.00%")
    return {"valid": True}

# TODO: Add endpoints for OCR and XML Generation

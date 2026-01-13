import os
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import List, Optional
from lib.fiscal_engine import calculate_fiscal_data
from lib.extraction_engine import extract_from_pdf

app = FastAPI(title="Notaria 4 Digital Core API")

class FiscalRequest(BaseModel):
    rfc_receptor: str
    monto_operacion: float
    valor_catastral: float
    is_vivienda: bool = True

@app.get("/")
def health_check():
    return {"status": "ok", "service": "Notaria 4 Digital Core"}

@app.post("/calculate-fiscal")
def calculate_fiscal(request: FiscalRequest):
    try:
        result = calculate_fiscal_data(
            rfc_receptor=request.rfc_receptor,
            monto_operacion=request.monto_operacion,
            valor_catastral=request.valor_catastral
        )
        return result
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.post("/extract-pdf")
def extract_pdf_data():
    # Placeholder for PDF extraction logic
    # In a real scenario, this would accept a file upload or a Storage URL
    return {"message": "Extraction endpoint ready"}

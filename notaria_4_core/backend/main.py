from fastapi import FastAPI, UploadFile, File, HTTPException
from pydantic import BaseModel
from typing import Optional
from decimal import Decimal
from lib.fiscal_engine import FiscalEngine
from lib.xml_generator import XMLGenerator

app = FastAPI(title="Notaría 4 Digital Core API")

class FiscalCalculationRequest(BaseModel):
    subtotal: float
    rfc_receptor: str
    precio_operacion: Optional[float] = None
    valor_catastral: Optional[float] = None

@app.get("/")
async def root():
    return {"status": "active", "system": "Notaría 4 Digital Core"}

@app.post("/calculate-taxes")
async def calculate_taxes(req: FiscalCalculationRequest):
    """
    Calculates retentions and local taxes based on input.
    """
    try:
        subtotal_dec = Decimal(str(req.subtotal))
        retentions = FiscalEngine.calculate_retentions(subtotal_dec, req.rfc_receptor)

        isai = None
        if req.precio_operacion and req.valor_catastral:
            precio_dec = Decimal(str(req.precio_operacion))
            catastral_dec = Decimal(str(req.valor_catastral))
            isai = FiscalEngine.calculate_isai(precio_dec, catastral_dec)

        return {
            "retentions": retentions,
            "isai": isai
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.post("/sanitize-name")
async def sanitize_name_endpoint(name: str):
    return {"original": name, "sanitized": FiscalEngine.sanitize_name(name)}

# Placeholder for OCR endpoint
@app.post("/extract-text")
async def extract_text(file: UploadFile = File(...)):
    return {"message": "OCR endpoint not fully implemented yet, but Tesseract is available in container."}

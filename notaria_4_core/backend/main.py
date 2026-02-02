from fastapi import FastAPI, UploadFile, File, HTTPException
from pydantic import BaseModel
from typing import List, Optional, Dict
from decimal import Decimal
from lib.fiscal_engine import calculate_retentions, calculate_isai, validate_copropiedad, sanitize_name

app = FastAPI(title="Notaría 4 Digital Core API")

class FiscalCalculationRequest(BaseModel):
    precio_operacion: float
    valor_catastral: float
    rfc_receptor: str
    subtotal_factura: float

class FiscalCalculationResponse(BaseModel):
    isai: float
    retentions: Dict[str, float]
    sanitized_rfc_len: int
    message: str

@app.get("/")
async def root():
    return {"status": "online", "system": "Notaría 4 Digital Core"}

@app.post("/extract-deed-data")
async def extract_deed_data(file: UploadFile = File(...)):
    """
    Uploads a PDF deed, performs OCR/NLP, and returns structured data.
    """
    # Placeholder for OCR logic
    return {"filename": file.filename, "status": "processing_started"}

@app.post("/calculate-fiscal", response_model=FiscalCalculationResponse)
async def calculate_fiscal(request: FiscalCalculationRequest):
    """
    Calculates ISAI and Retentions based on the input.
    """
    try:
        # Convert to Decimal
        price = Decimal(str(request.precio_operacion))
        catastral = Decimal(str(request.valor_catastral))
        subtotal = Decimal(str(request.subtotal_factura))
        rfc = request.rfc_receptor

        # Calculate
        isai = calculate_isai(price, catastral)
        retentions = calculate_retentions(subtotal, rfc)

        return {
            "isai": float(isai),
            "retentions": {k: float(v) for k, v in retentions.items()},
            "sanitized_rfc_len": len(rfc),
            "message": "Calculation successful"
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.post("/generate-xml")
async def generate_xml():
    """
    Generates the CFDI 4.0 XML with Notaries Complement.
    """
    # Placeholder for XML Generator
    return {"message": "XML Generation logic to be implemented"}

from fastapi import FastAPI, HTTPException, UploadFile, File
from pydantic import BaseModel
from decimal import Decimal
from typing import List, Optional, Dict, Any
from lib.fiscal_engine import calculate_isai, calculate_retentions, sanitize_name, validate_copropiedad
from lib.xml_generator import XMLGenerator
from lib.signer import cargar_signer
import os

app = FastAPI(title="Notaría 4 Digital Core API")

# Initialize resources
# In a real environment, we'd handle initialization errors more gracefully
signer = None
try:
    signer = cargar_signer()
except Exception:
    print("Warning: Signer could not be loaded (expected in development if no secrets)")

xml_gen = XMLGenerator(signer)

class FiscalCalculationRequest(BaseModel):
    precio_operacion: Decimal
    valor_catastral: Decimal
    rfc_receptor: str
    subtotal_factura: Decimal

class FiscalCalculationResponse(BaseModel):
    isai: Decimal
    retenciones: Dict[str, Decimal]

class CopropiedadRequest(BaseModel):
    percentages: List[Decimal]

@app.get("/")
async def root():
    return {"status": "Notaría 4 Core Online", "system": "Serverless Sovereign"}

@app.post("/calculate-fiscal", response_model=FiscalCalculationResponse)
async def calculate_fiscal(req: FiscalCalculationRequest):
    """
    Calculates ISAI and Retentions based on the input.
    """
    isai = calculate_isai(req.precio_operacion, req.valor_catastral)
    ret = calculate_retentions(req.subtotal_factura, req.rfc_receptor)
    return {"isai": isai, "retenciones": ret}

@app.post("/validate-copropiedad")
async def check_copropiedad(req: CopropiedadRequest):
    """
    Validates if copropiedad percentages sum to exactly 100.00%.
    """
    is_valid = validate_copropiedad(req.percentages)
    if not is_valid:
        raise HTTPException(status_code=400, detail="Percentages must sum to exactly 100.00%")
    return {"valid": True}

@app.post("/generate-xml")
async def generate_xml(factura_data: Dict[str, Any]):
    """
    Generates a signed CFDI 4.0 XML.
    Expects a JSON with 'emisor', 'receptor', 'conceptos', etc.
    """
    try:
        # In a real app, we would use Pydantic models for the complex nested structure
        # Here we pass the dict directly to our generator
        cfdi = xml_gen.generar_cfdi(factura_data, datos_complemento=factura_data.get('complemento_notarios'))
        return {"xml_signed": str(cfdi.xml_bytes())} # Returning bytes representation or base64
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/extract-deed-data")
async def extract_deed_data(file: UploadFile = File(...)):
    """
    Placeholder for the heavy OCR/NLP process running on Cloud Run.
    """
    # Logic: Save file -> Pytesseract -> SpaCy -> JSON
    return {"message": "Processing started", "filename": file.filename}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8080)

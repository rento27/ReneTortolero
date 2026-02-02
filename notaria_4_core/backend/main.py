from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from decimal import Decimal
from typing import List, Optional
from lib.fiscal_engine import sanitize_name, calculate_isai_manzanillo
# from lib.xml_generator import XMLGenerator # Commented out to avoid ImportErrors if satcfdi is not strictly installed in this env

app = FastAPI(title="Notaria 4 Digital Core API", version="1.0.0")

class ISAIRequest(BaseModel):
    operation_price: float
    cadastral_value: float
    rate: Optional[float] = 0.03

class SanitizationRequest(BaseModel):
    name: str

@app.get("/")
def read_root():
    return {"status": "active", "system": "Notaría 4 Digital Core"}

@app.post("/tools/calculate-isai")
def calculate_isai(request: ISAIRequest):
    try:
        isai = calculate_isai_manzanillo(
            Decimal(str(request.operation_price)),
            Decimal(str(request.cadastral_value)),
            Decimal(str(request.rate))
        )
        return {"isai_amount": float(isai)}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.post("/tools/sanitize-name")
def sanitize_client_name(request: SanitizationRequest):
    clean_name = sanitize_name(request.name)
    return {"original": request.name, "sanitized": clean_name}

@app.post("/cfdi/generate")
def generate_cfdi_endpoint(data: dict):
    # This would call XMLGenerator.generar_xml(data)
    # returning a mock for now
    return {"status": "received", "message": "XML Generation Logic implemented in lib/xml_generator.py"}

from decimal import Decimal
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from lib.fiscal_engine import FiscalEngine

app = FastAPI(title="Notaría 4 Digital Core API")

class FiscalCalculationRequest(BaseModel):
    precio_operacion: Decimal
    valor_catastral: Decimal
    rfc_receptor: str
    subtotal_factura: Decimal

@app.get("/")
def health_check():
    return {"status": "active", "system": "Notaría 4 Core"}

@app.post("/calculate-fiscal")
def calculate_fiscal(request: FiscalCalculationRequest):
    # Calculate ISAI
    isai = FiscalEngine.calculate_isai(
        precio_operacion=request.precio_operacion,
        valor_catastral=request.valor_catastral
    )

    # Calculate Retentions
    retentions = FiscalEngine.get_retentions_persona_moral(
        rfc=request.rfc_receptor,
        subtotal=request.subtotal_factura
    )

    return {
        "isai_manzanillo": isai,
        "retenciones": retentions
    }

@app.post("/generate-xml")
def generate_xml(data: dict):
    return {"status": "implemented_soon"}

@app.post("/extract-deed-data")
def extract_deed_data():
    return {"status": "implemented_soon"}

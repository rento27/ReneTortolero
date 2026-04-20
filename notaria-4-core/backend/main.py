from fastapi import FastAPI, HTTPException
from fiscal_rules import calculate_retentions, calculate_isai
from cfdi_engine import generar_xml
from pydantic import BaseModel
from typing import List, Optional

app = FastAPI(title="Notaría 4 Digital Core API")

class FacturaRequest(BaseModel):
    receptor_rfc: str
    subtotal: float
    municipio_receptor: str
    estado_receptor: str
    # ... other fields

class ISAIRequest(BaseModel):
    precio_operacion: float
    valor_catastral: float
    tasa_manzanillo: float = 0.03 # Default or fetched from config

@app.get("/")
def read_root():
    return {"status": "Notaría 4 Digital Core Active"}

@app.post("/calculate-isai")
def api_calculate_isai(request: ISAIRequest):
    return calculate_isai(request.precio_operacion, request.valor_catastral, request.tasa_manzanillo)

@app.post("/validate-rfc-retention")
def validate_rfc(rfc: str, subtotal: float):
    return calculate_retentions(rfc, subtotal)

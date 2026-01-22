from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import List, Optional
from decimal import Decimal
from lib.fiscal_engine import sanitize_name, calculate_retentions, calculate_isai_manzanillo, validate_copropiedad
from lib.xml_generator import generate_xml_structure, generar_complemento_notarios

app = FastAPI(title="Notaría 4 Digital Core API")

class FiscalRequest(BaseModel):
    rfc_receptor: str
    nombre_receptor: str
    subtotal: Decimal

class ISAIRequest(BaseModel):
    precio_operacion: Decimal
    valor_catastral: Decimal
    tasa: Optional[Decimal] = Decimal('0.03')

class CopropiedadRequest(BaseModel):
    porcentajes: List[Decimal]

@app.get("/")
def read_root():
    return {"message": "Notaría 4 Digital Core - Fiscal Engine Ready"}

@app.post("/calculate-fiscal")
def calculate_fiscal(request: FiscalRequest):
    sanitized_name = sanitize_name(request.nombre_receptor)
    retentions = calculate_retentions(request.subtotal, request.rfc_receptor)

    return {
        "sanitized_name": sanitized_name,
        "fiscal_data": retentions
    }

@app.post("/calculate-isai")
def calculate_isai(request: ISAIRequest):
    isai = calculate_isai_manzanillo(request.precio_operacion, request.valor_catastral, request.tasa)
    return {"isai_manzanillo": isai}

@app.post("/validate-copropiedad")
def check_copropiedad(request: CopropiedadRequest):
    is_valid = validate_copropiedad(request.porcentajes)
    if not is_valid:
        raise HTTPException(status_code=400, detail="La suma de porcentajes de copropiedad no es 100.00%")
    return {"status": "valid"}

@app.post("/generate-xml")
def generate_xml_endpoint(request: FiscalRequest):
    # Just a stub integration
    sanitized = sanitize_name(request.nombre_receptor)
    retentions = calculate_retentions(request.subtotal, request.rfc_receptor)

    factura_data = {
        "receptor": {"rfc": request.rfc_receptor, "nombre": sanitized},
        "subtotal": request.subtotal,
        "is_persona_moral": retentions['is_persona_moral']
    }

    xml_structure = generate_xml_structure(factura_data, {})
    return xml_structure

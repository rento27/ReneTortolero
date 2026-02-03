from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field
from typing import List, Optional
from decimal import Decimal
from lib.fiscal_engine import sanitize_name, get_retention_rates
from lib.xml_generator import generate_signed_xml

app = FastAPI(title="Notaria 4 Digital Core API")

class Receptor(BaseModel):
    rfc: str = Field(..., min_length=12, max_length=13, description="RFC del receptor")
    nombre: str = Field(..., description="Nombre o Razón Social")
    codigo_postal: str = Field(..., min_length=5, max_length=5)
    regimen_fiscal: str = Field(..., description="Clave del Régimen Fiscal (ej. 601)")

class Concepto(BaseModel):
    clave_prod_serv: str
    descripcion: str
    valor_unitario: Decimal
    cantidad: Decimal
    objeto_imp: str = Field(..., description="01: No objeto, 02: Sí objeto")
    clave_unidad: str

class CFDIRequest(BaseModel):
    receptor: Receptor
    conceptos: List[Concepto]
    uso_cfdi: str
    serie: Optional[str] = "A"
    folio: Optional[str] = None
    # Additional fields for Notary Complement would be added here

@app.get("/")
def read_root():
    return {"status": "ok", "service": "Notaria 4 Digital Core"}

@app.get("/health")
def health_check():
    return {"status": "healthy"}

@app.post("/api/v1/cfdi")
def create_cfdi(request: CFDIRequest):
    """
    Endpoint to generate a signed CFDI 4.0 XML.
    """
    try:
        # 1. Sanitize Inputs
        clean_name = sanitize_name(request.receptor.nombre)

        # 2. Determine Fiscal Rules (Retentions)
        retentions = get_retention_rates(request.receptor.rfc)

        # 3. Simulate XML Generation (Stub)
        # In a real implementation, we would map the Pydantic model to satcfdi objects
        # and include the Notaries Complement.
        xml_bytes = generate_signed_xml(request.model_dump())

        return {
            "status": "success",
            "message": "CFDI generated successfully (stub)",
            "data": {
                "sanitized_receptor_name": clean_name,
                "retentions_applied": retentions,
                "xml_preview_length": len(xml_bytes)
            }
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

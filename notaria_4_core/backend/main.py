from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import Dict, Any, Optional
import sys
import os

# Ensure lib is in path if running from backend root
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from lib.xml_generator import generar_factura
from lib.signer import load_signer

app = FastAPI(title="Notaria 4 Digital Core Backend")

class CFDIRequest(BaseModel):
    datos_factura: Dict[str, Any]
    datos_complemento: Optional[Dict[str, Any]] = None

@app.get("/")
def read_root():
    return {"status": "ok", "service": "Notaria 4 Digital Core"}

@app.post("/api/v1/cfdi")
def create_cfdi(request: CFDIRequest):
    try:
        # Load signer (mock or real)
        signer = load_signer()

        # Generate CFDI
        cfdi = generar_factura(request.datos_factura, request.datos_complemento, signer=signer)

        # Return XML string
        # satcfdi object to bytes
        return {"xml": cfdi.xml_bytes().decode('utf-8')}
    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=400, detail=str(e))

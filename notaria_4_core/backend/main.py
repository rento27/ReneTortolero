from fastapi import FastAPI, HTTPException, Body
from pydantic import BaseModel
from typing import List, Optional
from decimal import Decimal
from lib.fiscal_engine import calculate_isai, sanitize_name, validate_postal_code_structure
from lib.xml_generator import XMLGenerator
from lib.signer import load_signer
import os

app = FastAPI(title="Notaría 4 Digital Core API")

# Load Signer
# In production, this should be done at startup or lazily
try:
    signer = load_signer(test_mode=os.getenv("TEST_MODE", "False").lower() == "true")
except Exception as e:
    print(f"Warning: Could not load signer: {e}")
    signer = None

class ISAIRequest(BaseModel):
    operation_price: Decimal
    cadastral_value: Decimal
    rate: Optional[Decimal] = Decimal("0.03")

class CFDIRequest(BaseModel):
    # Simplified model for request validation
    emisor: dict
    receptor: dict
    conceptos: List[dict]
    notario_data: Optional[dict] = None

@app.post("/api/v1/isai")
def get_isai(request: ISAIRequest):
    isai = calculate_isai(request.operation_price, request.cadastral_value, request.rate)
    return {"isai": isai}

@app.post("/api/v1/cfdi")
def create_cfdi(request: CFDIRequest):
    # Validate Postal Code against catalog (mock implementation for now)
    # In production, this should query Firestore c_CodigoPostal
    receptor_cp = request.receptor.get('codigo_postal', '')
    if not validate_postal_code_structure(receptor_cp):
        raise HTTPException(status_code=400, detail="Invalid Postal Code structure")

    # Placeholder for catalog validation
    # if not db.lookup_postal_code(receptor_cp): ...

    try:
        generator = XMLGenerator(signer=signer)
        # request.dict() is deprecated in Pydantic v2, use model_dump() if v2, but v1 is common.
        # Assuming v1 or v2 compatible usage for now.
        cfdi = generator.generate_cfdi(request.dict())

        # cfdi.xml_bytes() returns bytes, decode to string
        return {"xml": cfdi.xml_bytes().decode("utf-8")}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.get("/health")
def health():
    return {"status": "ok"}

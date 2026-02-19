from fastapi import FastAPI, HTTPException
from typing import List, Optional, Any
from decimal import Decimal
import base64
from lib.fiscal_engine import sanitize_name, calculate_isai_manzanillo, calculate_retentions, validate_postal_code
from lib.xml_generator import generate_signed_xml
from lib.api_models import InvoiceRequest, Receptor, Concepto, Copropietario
from lib.complement_notarios import create_complemento_notarios

app = FastAPI(title="Notaria 4 Digital Core API", version="1.0.0")

@app.get("/health")
def health_check():
    return {"status": "ok", "service": "notaria-4-core-backend"}

@app.post("/api/v1/cfdi")
def create_cfdi(request: InvoiceRequest):
    # 1. Sanitize Receptor Name
    request.receptor.nombre = sanitize_name(request.receptor.nombre)

    # 1.1 Validate Postal Code
    if not validate_postal_code(request.receptor.domicilio_fiscal):
         raise HTTPException(status_code=400, detail=f"Invalid Postal Code: {request.receptor.domicilio_fiscal}")

    # 2. Calculate Retentions (Logic Check)
    retentions = calculate_retentions(
        request.receptor.rfc,
        request.subtotal
    )

    # 3. Create Complemento Notarios (if present)
    complemento_obj = None
    if request.complemento_notarios:
        try:
            complemento_obj = create_complemento_notarios(request.complemento_notarios)
        except ValueError as ve:
            raise HTTPException(status_code=400, detail=f"Complement Validation Error: {str(ve)}")

    # 4. Generate XML
    try:
        data = request.model_dump()

        # Pass the pre-constructed satcfdi complement object
        xml_bytes = generate_signed_xml(data, complemento=complemento_obj)

        return {
            "status": "success",
            "xml_base64": base64.b64encode(xml_bytes).decode('utf-8'),
            "retentions_calculated": retentions
        }
    except ValueError as ve:
        raise HTTPException(status_code=400, detail=f"Validation Error: {str(ve)}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/")
def root():
    return {"message": "Notaria 4 Digital Core API"}

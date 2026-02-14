from fastapi import FastAPI, HTTPException
from typing import Dict, Any
from lib.fiscal_engine import sanitize_name, calculate_retentions, validate_postal_code
from lib.xml_generator import generate_signed_xml
from lib.api_models import InvoiceRequest

app = FastAPI(title="Notaria 4 Digital Core API", version="1.0.0")

@app.get("/health")
def health_check():
    return {"status": "ok", "service": "notaria-4-core-backend"}

@app.post("/api/v1/cfdi")
def create_cfdi(request: InvoiceRequest):
    # Pydantic v2
    data = request.model_dump()

    # 1. Sanitize Receptor Name
    data['receptor']['nombre'] = sanitize_name(data['receptor']['nombre'])

    # 1.1 Validate Postal Code
    if not validate_postal_code(data['receptor']['domicilio_fiscal']):
         raise HTTPException(status_code=400, detail=f"Invalid Postal Code: {data['receptor']['domicilio_fiscal']}")

    # 2. Calculate Retentions (Logic Check)
    retentions = calculate_retentions(
        data['receptor']['rfc'],
        data['subtotal']
    )

    # 3. Generate XML
    try:
        xml_bytes = generate_signed_xml(data)
        return {
            "status": "success",
            "xml_base64": xml_bytes.decode('utf-8'),
            "retentions_calculated": retentions
        }
    except ValueError as ve:
        raise HTTPException(status_code=400, detail=f"Validation Error: {str(ve)}")
    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/")
def root():
    return {"message": "Notaria 4 Digital Core API"}

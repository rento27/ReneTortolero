from fastapi import FastAPI, HTTPException
from decimal import Decimal
from lib.fiscal_engine import sanitize_name, calculate_isai_manzanillo, calculate_retentions, validate_postal_code
from lib.xml_generator import generate_signed_xml
from lib.api_models import InvoiceRequest

app = FastAPI(title="Notaria 4 Digital Core API", version="1.0.0")

@app.get("/health")
def health_check():
    return {"status": "ok", "service": "notaria-4-core-backend"}

@app.post("/api/v1/cfdi")
def create_cfdi(request: InvoiceRequest):
    # 1. Sanitize Receptor Name
    # We update the model directly
    sanitized_name = sanitize_name(request.receptor.nombre)
    request.receptor.nombre = sanitized_name

    # 1.1 Validate Postal Code
    if not validate_postal_code(request.receptor.domicilio_fiscal):
         raise HTTPException(status_code=400, detail=f"Invalid Postal Code: {request.receptor.domicilio_fiscal}")

    # 2. Calculate Retentions (for response visibility only)
    # This logic is duplicated here for response purposes,
    # but the authoritative logic for XML is in xml_generator.
    retentions = calculate_retentions(
        request.receptor.rfc,
        request.subtotal
    )

    # 3. Generate XML
    try:
        # Pass the Pydantic model
        xml_bytes = generate_signed_xml(request)

        return {
            "status": "success",
            "xml_base64": xml_bytes.decode('utf-8', errors='replace'), # Ensure string output
            "retentions_calculated": retentions
        }
    except ValueError as ve:
        raise HTTPException(status_code=400, detail=f"Validation Error: {str(ve)}")
    except Exception as e:
        # In production, log e
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/v1/calculate-isai")
def calculate_isai(operation_price: Decimal, cadastral_value: Decimal):
    isai = calculate_isai_manzanillo(operation_price, cadastral_value)
    return {"isai": isai}

@app.get("/")
def root():
    return {"message": "Notaria 4 Digital Core API"}

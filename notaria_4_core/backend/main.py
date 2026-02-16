from fastapi import FastAPI, HTTPException
from typing import Optional
from decimal import Decimal, ROUND_HALF_UP
from lib.fiscal_engine import sanitize_name, calculate_isai_manzanillo, calculate_retentions, validate_postal_code
from lib.xml_generator import generate_signed_xml
from lib.api_models import InvoiceRequest, ISAIRequest

app = FastAPI(title="Notaria 4 Digital Core API", version="1.0.0")

@app.get("/health")
def health_check():
    return {"status": "ok", "service": "notaria-4-core-backend"}

@app.post("/api/v1/cfdi")
def create_cfdi(request: InvoiceRequest):
    # 1. Validate Postal Code
    # Assuming the API receives the 'domicilio_fiscal' as the CP code
    if not validate_postal_code(request.receptor.domicilio_fiscal):
         raise HTTPException(status_code=400, detail=f"Invalid Postal Code: {request.receptor.domicilio_fiscal}")

    # 2. Generate XML
    try:
        # Note: XML Generator handles name sanitization and tax calculations internally for the XML
        xml_bytes = generate_signed_xml(request)

        # Calculate retentions for response summary (using total subtotal provided or calculated)
        # To ensure consistency with XML (where satcfdi calculates Importe from Quantity * UnitValue),
        # we recalculate the subtotal here based on the same logic.

        # Calculate subtotal as sum of (Quantity * Unit Value) for each concept
        # We round each concept amount to 2 decimals as standard practice before summing
        subtotal = sum((c.cantidad * c.valor_unitario).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP) for c in request.conceptos)

        retentions = calculate_retentions(
            request.receptor.rfc,
            subtotal
        )

        # In a real scenario, we might upload this to storage and return a URL
        # For now, return the stub content
        return {
            "status": "success",
            "xml_base64": xml_bytes.decode('utf-8', errors='replace'), # Decode bytes to string
            "retentions_calculated": retentions
        }
    except ValueError as ve:
        raise HTTPException(status_code=400, detail=f"Validation Error: {str(ve)}")
    except Exception as e:
        # Log error in production
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/v1/calculate-isai")
def calculate_isai(request: ISAIRequest):
    try:
        isai = calculate_isai_manzanillo(
            operation_price=request.valor_operacion,
            cadastral_value=request.valor_catastral,
            rate=request.tasa or Decimal("0.03")
        )
        return {
            "isai_amount": isai,
            "formula": "Max(ValorOperacion, ValorCatastral) * Tasa",
            "base_gravable": max(request.valor_operacion, request.valor_catastral)
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/")
def root():
    return {"message": "Notaria 4 Digital Core API"}

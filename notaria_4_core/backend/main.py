import base64
from fastapi import FastAPI, HTTPException
from decimal import Decimal
from lib.fiscal_engine import sanitize_name, calculate_isai_manzanillo, calculate_retentions, validate_postal_code
from lib.xml_generator import generate_signed_xml
from lib.api_models import InvoiceRequest, ISAIRequest, ExtractDataRequest
from lib.ocr_engine import extract_data

app = FastAPI(title="Notaria 4 Digital Core API", version="1.0.0")

@app.get("/health")
def health_check():
    return {"status": "ok", "service": "notaria-4-core-backend"}

@app.post("/api/v1/cfdi")
def create_cfdi(request: InvoiceRequest):
    # Pydantic v2 compatibility
    data = request.model_dump()

    # 1. Sanitize Receptor Name
    data['receptor']['nombre'] = sanitize_name(data['receptor']['nombre'])

    # 1.1 Validate Postal Code
    # Assuming the API receives the 'domicilio_fiscal' as the CP code
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
        # In a real scenario, we might upload this to storage and return a URL
        # For now, return the content as base64 encoded string
        xml_base64 = base64.b64encode(xml_bytes).decode('utf-8')
        return {
            "status": "success",
            "xml_base64": xml_base64,
            "retentions_calculated": retentions
        }
    except ValueError as ve:
        raise HTTPException(status_code=400, detail=f"Validation Error: {str(ve)}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/v1/calculate-isai")
def calculate_isai(request: ISAIRequest):
    try:
        isai_amount = calculate_isai_manzanillo(
            operation_price=request.precio_operacion,
            cadastral_value=request.valor_catastral,
            rate=request.tasa
        )
        return {
            "status": "success",
            "isai_amount": isai_amount
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.post("/api/v1/extract-data")
def extract_document_data(request: ExtractDataRequest):
    try:
        result = extract_data(request.file_base64)
        if "error" in result:
             raise HTTPException(status_code=500, detail=result["error"])
        return {
            "status": "success",
            "data": result
        }
    except Exception as e:
         raise HTTPException(status_code=500, detail=str(e))

@app.get("/")
def root():
    return {"message": "Notaria 4 Digital Core API"}

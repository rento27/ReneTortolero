from fastapi import FastAPI, HTTPException, UploadFile, File
from decimal import Decimal
from lib.api_models import InvoiceRequest, ISAIRequest
from lib.fiscal_engine import sanitize_name, calculate_isai_manzanillo, calculate_retentions, validate_postal_code
from lib.xml_generator import generate_signed_xml

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
        # For now, return the stub content
        import base64
        return {
            "status": "success",
            "xml_base64": base64.b64encode(xml_bytes).decode('utf-8'),
            "retentions_calculated": retentions
        }
    except ValueError as ve:
        raise HTTPException(status_code=400, detail=f"Validation Error: {str(ve)}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/v1/calculate-isai")
def calculate_isai(request: ISAIRequest):
    # The default rate is typically stored in Remote Config, for now we will use the default parameter
    try:
        isai = calculate_isai_manzanillo(request.precio_operacion, request.valor_catastral)
        return {"status": "success", "isai": isai}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/v1/extract-data")
def extract_data(file: UploadFile = File(...)):
    try:
        from lib.ocr_engine import extract_data_from_pdf
        import os
        import uuid

        # Save uploaded file temporarily with a secure random name
        temp_filename = f"{uuid.uuid4().hex}.pdf"
        temp_path = f"/tmp/{temp_filename}"
        try:
            with open(temp_path, "wb") as buffer:
                import shutil
                shutil.copyfileobj(file.file, buffer)

            result = extract_data_from_pdf(temp_path)
            return {"status": "success", "data": result}
        finally:
            # Clean up
            if os.path.exists(temp_path):
                os.remove(temp_path)
    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/")
def root():
    return {"message": "Notaria 4 Digital Core API"}

from fastapi import FastAPI, HTTPException, UploadFile, File
from lib.api_models import InvoiceRequest, ISAIRequest
from lib.fiscal_engine import sanitize_name, calculate_retentions, validate_postal_code, calculate_isai_manzanillo
from lib.xml_generator import generate_signed_xml
from lib.ocr_engine import extract_text_from_pdf, extract_structured_data

app = FastAPI(title="Notaria 4 Digital Core API", version="1.0.0")

@app.get("/health")
def health_check():
    return {"status": "ok", "service": "notaria-4-core-backend"}

@app.post("/api/v1/calculate-isai")
def calculate_isai(request: ISAIRequest):
    try:
        kwargs = {}
        if request.tasa is not None:
            kwargs['rate'] = request.tasa

        result = calculate_isai_manzanillo(
            operation_price=request.precio_operacion,
            cadastral_value=request.valor_catastral,
            **kwargs
        )
        return {
            "status": "success",
            "isai_amount": result,
            "base": max(request.precio_operacion, request.valor_catastral)
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/v1/extract-data")
async def extract_data(file: UploadFile = File(...)):
    if file.content_type != "application/pdf":
        raise HTTPException(status_code=400, detail="Only PDF files are supported")

    contents = await file.read()
    text = extract_text_from_pdf(contents)
    data = extract_structured_data(text)

    return {
        "status": "success",
        "extracted_data": data,
        "text_preview": text[:500] + "..." if len(text) > 500 else text
    }

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
        return {
            "status": "success",
            "xml_base64": xml_bytes.decode('utf-8'), # Stub returns simple string bytes
            "retentions_calculated": retentions
        }
    except ValueError as ve:
        raise HTTPException(status_code=400, detail=f"Validation Error: {str(ve)}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/")
def root():
    return {"message": "Notaria 4 Digital Core API"}

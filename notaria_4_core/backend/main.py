from fastapi import FastAPI, HTTPException, UploadFile, File
from lib.api_models import InvoiceRequest, ISAIRequest
from lib.fiscal_engine import sanitize_name, calculate_isai_manzanillo, calculate_retentions, validate_postal_code
from lib.xml_generator import generate_signed_xml
from lib.ocr_engine import extract_text_from_pdf
import base64

app = FastAPI(title="Notaria 4 Digital Core API", version="1.0.0")

@app.get("/health")
def health_check():
    return {"status": "ok", "service": "notaria-4-core-backend"}

@app.post("/api/v1/cfdi")
def create_cfdi(request: InvoiceRequest):
    # Pydantic v2 compatibility
    data = request.model_dump()

    # 1. Validate Postal Code
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
        isai_value = calculate_isai_manzanillo(request.operation_price, request.cadastral_value)
        return {"status": "success", "isai": str(isai_value)}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/v1/extract-data")
async def extract_data(file: UploadFile = File(...)):
    try:
        pdf_bytes = await file.read()
        extracted_text = extract_text_from_pdf(pdf_bytes)
        return {"status": "success", "extracted_text": extracted_text}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/")
def root():
    return {"message": "Notaria 4 Digital Core API"}

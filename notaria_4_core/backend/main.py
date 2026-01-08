from fastapi import FastAPI, UploadFile, File, HTTPException
from pydantic import BaseModel
from decimal import Decimal
import os

# Local imports
from lib.fiscal_engine import FiscalEngine
from lib.extraction_engine import ExtractionEngine
from lib.xml_generator import XMLGenerator

app = FastAPI(
    title="Notaría 4 Digital Core API",
    description="Backend for Notaría 4 Manzanillo. Handles CFDI 4.0, OCR, and Fiscal Logic.",
    version="1.0.0"
)

# --- Models ---
class FiscalRequest(BaseModel):
    subtotal: float
    rfc_receptor: str

class IsaiRequest(BaseModel):
    operation_price: float
    cadastral_value: float
    rate: float

class SanitizeRequest(BaseModel):
    name: str

class XMLPreviewRequest(BaseModel):
    emisor: dict
    receptor: dict
    items: list
    notary_data: dict = None

# --- Endpoints ---

@app.get("/")
async def root():
    return {"status": "active", "service": "Notaría 4 Digital Core", "version": "1.0.0"}

@app.get("/health")
async def health_check():
    return {"status": "healthy"}

@app.post("/fiscal/calculate-retentions")
async def calculate_retentions_endpoint(req: FiscalRequest):
    """
    Calculates ISR and IVA retentions for Personas Morales.
    """
    try:
        results = FiscalEngine.calculate_retentions(Decimal(str(req.subtotal)), req.rfc_receptor)
        return results
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.post("/fiscal/calculate-isai")
async def calculate_isai_endpoint(req: IsaiRequest):
    """
    Calculates ISAI based on Manzanillo rules.
    """
    try:
        result = FiscalEngine.calculate_isai_manzanillo(
            Decimal(str(req.operation_price)),
            Decimal(str(req.cadastral_value)),
            Decimal(str(req.rate))
        )
        return {"isai_amount": result}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.post("/fiscal/sanitize-name")
async def sanitize_name_endpoint(req: SanitizeRequest):
    """
    Cleans client name for CFDI 4.0 (removes S.A. DE C.V., etc.)
    """
    cleaned = FiscalEngine.sanitize_name(req.name)
    return {"original": req.name, "sanitized": cleaned}

@app.post("/extract/document")
async def extract_document_endpoint(file: UploadFile = File(...)):
    """
    Uploads a PDF/Image and returns extracted text and entities.
    """
    try:
        contents = await file.read()
        text = ExtractionEngine.extract_text(contents, file.filename)
        entities = ExtractionEngine.extract_entities(text)
        return {
            "text_preview": text[:500] + "...",
            "text_length": len(text),
            "entities": entities
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/xml/preview")
async def preview_xml_endpoint(req: XMLPreviewRequest):
    """
    Generates an unsigned XML preview for validation.
    """
    try:
        cfdi = XMLGenerator.generate_invoice_xml(
            emisor_data=req.emisor,
            receptor_data=req.receptor,
            items=req.items,
            notary_data=req.notary_data
        )
        # Convert to string/bytes
        xml_bytes = cfdi.xml_bytes()
        return {"xml_content": xml_bytes.decode("utf-8")}
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"XML Generation Error: {str(e)}")

if __name__ == "__main__":
    import uvicorn
    port = int(os.environ.get("PORT", 8080))
    uvicorn.run(app, host="0.0.0.0", port=port)

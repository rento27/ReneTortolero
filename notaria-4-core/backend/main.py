from fastapi import FastAPI, HTTPException, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from lib.fiscal_engine import FiscalEngine
from lib.extraction_engine import ExtractionEngine
from lib.xml_generator import XMLGenerator
from lib.security import SecurityManager
import os

app = FastAPI(title="Notaría 4 Digital Core API")

# Enable CORS for frontend development
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize managers
fiscal_engine = FiscalEngine()
security_manager = SecurityManager()
extraction_engine = ExtractionEngine()
# signer = security_manager.load_signer() # Mocked inside
xml_generator = XMLGenerator(signer=None)

class FacturaRequest(BaseModel):
    receptor_rfc: str
    razon_social: str
    subtotal: float
    escritura: str = ""
    # Add other fields as necessary

@app.get("/")
def read_root():
    return {"message": "Notaría 4 Digital Core API is running"}

@app.post("/api/v1/generate-cfdi")
def generate_cfdi(request: FacturaRequest):
    """
    Generates a valid CFDI 4.0 XML based on the request.
    Handles 'Persona Moral' logic and ISAI calculations automatically.
    """
    try:
        # 1. Validate Receiver Type (Moral vs Fisica)
        is_moral = fiscal_engine.is_persona_moral(request.receptor_rfc)

        # 2. Calculate Taxes
        taxes = fiscal_engine.calculate_taxes(request.subtotal, is_moral)

        # 3. Generate XML Structure
        # We pass the pydantic model as a dict
        cfdi = xml_generator.generate_cfdi(request.model_dump(), taxes)

        # 4. Serialize
        # xml_bytes = cfdi.xml_bytes()
        # For now, return the structure as JSON for inspection since we don't have keys to sign

        return {
            "status": "success",
            "is_persona_moral": is_moral,
            "calculations": taxes,
            "xml_preview": str(cfdi), # Representation of the object
            "message": "CFDI generated (unsigned)"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/v1/process-deed")
async def process_deed(file: UploadFile = File(...)):
    """
    Receives a PDF deed, performs OCR/NLP, and returns structured data.
    """
    try:
        content = await file.read()

        # 1. Extract raw text (OCR if needed)
        text = extraction_engine.extract_text_from_pdf(content)

        # 2. Extract structured entities (NLP/Regex)
        data = extraction_engine.extract_entities(text)

        return {
            "status": "success",
            "filename": file.filename,
            "extracted_data": data
        }
    except Exception as e:
        print(f"Error processing deed: {e}")
        raise HTTPException(status_code=500, detail=str(e))

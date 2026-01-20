import os
import shutil
import tempfile
from decimal import Decimal
from typing import List, Optional, Dict, Any

from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

# Import core libraries
from backend.lib.extraction_engine import ExtractionEngine
from backend.lib.fiscal_engine import calculate_taxes, calculate_isai, validate_zip_code, sanitize_name
from backend.lib.xml_generator import generate_xml

app = FastAPI(title="Notaría 4 Digital Core API")

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Adjust for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize engines
extraction_engine = ExtractionEngine()

# Pydantic Models
class FiscalCalculationRequest(BaseModel):
    subtotal: Decimal
    rfc_receptor: str

class ISAICalculationRequest(BaseModel):
    precio_operacion: Decimal
    valor_catastral: Decimal
    tasa: Optional[Decimal] = Decimal('0.03')

class XMLGenerationRequest(BaseModel):
    emisor: Dict[str, Any]
    receptor: Dict[str, Any]
    conceptos: List[Dict[str, Any]]
    datos_notario: Dict[str, Any]

@app.get("/")
def health_check():
    return {"status": "ok", "service": "notaria-4-core"}

@app.post("/extract-deed-data")
async def extract_deed_data(file: UploadFile = File(...)):
    """
    Receives a PDF deed, extracts text using OCR/PyMuPDF, and parses entities using NLP/Regex.
    """
    if not file.filename.endswith('.pdf'):
        raise HTTPException(status_code=400, detail="Only PDF files are supported")

    # Save uploaded file to temp
    with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp:
        shutil.copyfileobj(file.file, tmp)
        tmp_path = tmp.name

    try:
        # Extract Text
        text = extraction_engine.extract_text(tmp_path)

        # Parse Entities
        entities = extraction_engine.parse_entities(text)

        return {
            "status": "success",
            "extracted_data": entities,
            "raw_text_preview": text[:500] + "..." # Preview
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Extraction failed: {str(e)}")
    finally:
        # Cleanup
        if os.path.exists(tmp_path):
            os.remove(tmp_path)

@app.post("/calculate-fiscal")
async def calculate_fiscal_endpoint(request: FiscalCalculationRequest):
    """
    Calculates taxes including Persona Moral retentions.
    """
    try:
        # Sanitize Name (if passed, but here we only have RFC in request for calc)
        # We can add name sanitization endpoint separately or include it here if request changes.

        result = calculate_taxes(request.subtotal, request.rfc_receptor)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/calculate-isai")
async def calculate_isai_endpoint(request: ISAICalculationRequest):
    """
    Calculates ISAI for Manzanillo.
    """
    try:
        impuesto = calculate_isai(request.precio_operacion, request.valor_catastral, request.tasa)
        return {"isai_amount": impuesto}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/generate-xml")
async def generate_xml_endpoint(request: XMLGenerationRequest):
    """
    Generates the CFDI 4.0 object structure (unsigned for now, unless signer is configured).
    """
    try:
        # Validate ZIP if receptor has it
        receptor = request.receptor
        zip_code = receptor.get("DomicilioFiscalReceptor") or receptor.get("CodigoPostal")
        if zip_code:
            if not validate_zip_code(zip_code):
                 raise HTTPException(status_code=400, detail=f"Invalid ZIP Code for Colima context: {zip_code}")

        # Sanitize Receptor Name
        if "Nombre" in receptor:
            receptor["Nombre"] = sanitize_name(receptor["Nombre"])

        # Generate (Mocking signer as None for API usage without keys loaded)
        cfdi = generate_xml(
            emisor=request.emisor,
            receptor=request.receptor,
            conceptos=request.conceptos,
            datos_notario=request.datos_notario
        )

        # Serialize to JSON (satcfdi objects are dict-like or have to_json/dump)
        # Using generic dict conversion for response
        return cfdi

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

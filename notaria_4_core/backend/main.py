import os
from fastapi import FastAPI, HTTPException, UploadFile, File
from pydantic import BaseModel
from decimal import Decimal
from typing import List, Optional, Dict, Any

from lib.fiscal_engine import sanitize_name, calculate_retentions, validate_copropiedad, calculate_isai
from lib.extraction_engine import ExtractionEngine
from lib.xml_generator import generar_xml

app = FastAPI(title="Notaría 4 Digital Core API")

extraction_engine = ExtractionEngine()

class FiscalRequest(BaseModel):
    rfc_receptor: str
    nombre_receptor: str
    subtotal: Decimal

class ISAIRequest(BaseModel):
    precio_operacion: Decimal
    valor_catastral: Decimal
    tasa: Decimal # Should come from Remote Config, but passed here for calculation

class CopropiedadRequest(BaseModel):
    porcentajes: List[Decimal]

class XMLGenRequest(BaseModel):
    datos_factura: Dict[str, Any]
    datos_notario: Dict[str, Any]

@app.get("/")
def health_check():
    return {"status": "ok", "service": "Notaría 4 Core"}

@app.post("/calculate-fiscal")
def calculate_fiscal_data(req: FiscalRequest):
    """
    Calculates retentions and sanitizes name.
    """
    sanitized_name = sanitize_name(req.nombre_receptor)
    retentions = calculate_retentions(req.rfc_receptor, req.subtotal)

    return {
        "sanitized_name": sanitized_name,
        "retentions": retentions
    }

@app.post("/calculate-isai")
def calculate_isai_endpoint(req: ISAIRequest):
    isai = calculate_isai(req.precio_operacion, req.valor_catastral, req.tasa)
    return {"isai_amount": isai}

@app.post("/validate-copropiedad")
def validate_copropiedad_endpoint(req: CopropiedadRequest):
    is_valid = validate_copropiedad(req.porcentajes)
    if not is_valid:
        raise HTTPException(status_code=400, detail="Percentages do not sum to exactly 100.00%")
    return {"valid": True}

@app.post("/extract-deed-data")
async def extract_deed_data(file: UploadFile = File(...)):
    """
    Upload a PDF deed (Escritura) to extract text and entities.
    Uses Hybrid approach: PyMuPDF -> Tesseract OCR -> Regex/NLP.
    """
    try:
        contents = await file.read()
        # Extract text
        text = extraction_engine.extract_text_from_pdf(contents)
        # Parse entities
        entities = extraction_engine.parse_entities(text)

        return {
            "success": True,
            "extracted_text_preview": text[:500], # Preview first 500 chars
            "entities": entities
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/generate-xml")
def generate_xml_endpoint(req: XMLGenRequest):
    """
    Generates the CFDI 4.0 XML with Notarios Complement.
    """
    try:
        # Generate the CFDI object
        cfdi = generar_xml(req.datos_factura, req.datos_notario)

        # Serialize to XML string
        # Assuming satcfdi Comprobante has .xml_bytes() or similar.
        # If running in environment without satcfdi installed, this might fail,
        # so we wrap in try/except or return string representation if possible.
        if hasattr(cfdi, 'xml_bytes'):
             xml_content = cfdi.xml_bytes().decode("utf-8")
        else:
             # Fallback or mock behavior if library version differs
             xml_content = str(cfdi)

        return {"xml_content": xml_content}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error generating XML: {str(e)}")

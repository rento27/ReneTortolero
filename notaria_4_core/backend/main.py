from fastapi import FastAPI, HTTPException, UploadFile, File
from pydantic import BaseModel
from typing import List, Optional, Dict, Any
from decimal import Decimal
import tempfile
import os

from lib.fiscal_engine import FiscalEngine
from lib.extraction_engine import ExtractionEngine
from lib.xml_generator import XMLGenerator
# from lib.signer import SecureSigner # Requires GCP credentials, keeping import ready

app = FastAPI(title="Notaría 4 Digital Core API")

class FiscalCalculationRequest(BaseModel):
    rfc_receptor: str
    subtotal: float
    is_persona_moral: bool = False

class CFDIRequest(BaseModel):
    emisor_rfc: str
    emisor_name: str
    emisor_regimen: str
    lugar_expedicion: str
    receptor: Dict[str, Any]
    conceptos: List[Dict[str, Any]]
    subtotal: float
    is_persona_moral: bool
    datos_operacion: Optional[Dict[str, Any]] = None

@app.get("/")
async def root():
    return {"status": "ok", "service": "Notaría 4 Digital Core Backend"}

@app.post("/calculate-fiscal")
async def calculate_fiscal(request: FiscalCalculationRequest):
    """
    Calculates taxes and retentions based on business rules.
    """
    try:
        engine = FiscalEngine()

        # Determine if Persona Moral based on RFC length if not explicitly provided
        # RFC Persona Moral is 12 chars, Fisica is 13.
        is_moral = len(request.rfc_receptor) == 12

        result = engine.calculate_taxes(
            amount=request.subtotal,
            is_persona_moral=is_moral
        )
        return result
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.post("/upload-deed")
async def upload_deed(file: UploadFile = File(...)):
    """
    Uploads a PDF deed, extracts text via hybrid OCR, and returns raw text.
    """
    try:
        # Save temp file
        with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp:
            content = await file.read()
            tmp.write(content)
            tmp_path = tmp.name

        extractor = ExtractionEngine()
        text = extractor.extract_text_from_pdf(tmp_path)
        entities = extractor.extract_entities(text)

        # Cleanup
        os.remove(tmp_path)

        return {"text": text, "entities": entities}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/generate-cfdi")
async def generate_cfdi(request: CFDIRequest):
    """
    Generates a CFDI 4.0 XML structure.
    Note: Real signing would happen here using SecureSigner.
    """
    try:
        generator = XMLGenerator(
            emisor_rfc=request.emisor_rfc,
            emisor_name=request.emisor_name,
            emisor_regimen=request.emisor_regimen,
            lugar_expedicion=request.lugar_expedicion
        )

        # Generate Complement Data if provided
        complemento_dict = None
        if request.datos_operacion:
            complemento_dict = generator.generar_complemento_notarios(request.datos_operacion)

        # Process Conceptos decimal conversion
        processed_conceptos = []
        for c in request.conceptos:
            # We assume input is JSON float, convert to Decimal/Proper format for generator
            c_copy = c.copy()
            c_copy['amount'] = Decimal(str(c['amount']))
            c_copy['valor_unitario'] = Decimal(str(c['valor_unitario']))
            c_copy['cantidad'] = Decimal(str(c['cantidad']))
            processed_conceptos.append(c_copy)

        cfdi = generator.generar_xml(
            receptor_data=request.receptor,
            conceptos=processed_conceptos,
            subtotal=Decimal(str(request.subtotal)),
            is_persona_moral=request.is_persona_moral,
            datos_complemento=complemento_dict
        )

        # In a real scenario, we would sign here:
        # signer = SecureSigner(...).load_signer()
        # signed_cfdi = cfdi.sign(signer)
        # return {"xml": signed_cfdi.xml_bytes().decode('utf-8')}

        # For now, we return the dict structure as verification
        return {"status": "generated", "structure_preview": str(cfdi)}

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

from fastapi import FastAPI, UploadFile, File, HTTPException
from pydantic import BaseModel
from typing import List, Optional, Dict, Any
from decimal import Decimal
from lib.fiscal_engine import FiscalEngine
from lib.xml_generator import XMLGenerator
from lib.signer import cargar_signer

app = FastAPI(title="Notaría 4 Digital Core API")
fiscal_engine = FiscalEngine()

try:
    signer = cargar_signer()
except Exception as e:
    print(f"Warning: Could not load signer: {e}")
    signer = None

xml_generator = XMLGenerator(signer=signer)

@app.get("/")
def read_root():
    return {"status": "active", "service": "Notaría 4 Digital Core"}

class ExtractRequest(BaseModel):
    file_url: str

@app.post("/extract-deed-data")
def extract_deed_data(file: UploadFile = File(...)):
    """
    Endpoint to extract data from a Deed PDF (Escritura).
    Uses PyMuPDF -> Tesseract -> SpaCy pipeline.
    """
    return {"filename": file.filename, "status": "processing_started"}

class FiscalCalculationRequest(BaseModel):
    subtotal: float
    rfc_receptor: str
    is_manzanillo: bool
    operation_price: Optional[float] = 0.0
    catastral_value: Optional[float] = 0.0

@app.post("/calculate-fiscal")
def calculate_fiscal_endpoint(req: FiscalCalculationRequest):
    """
    Endpoint to calculate taxes based on strict Notaría 4 rules.
    """
    try:
        subtotal_dec = Decimal(str(req.subtotal))
        operation_price_dec = Decimal(str(req.operation_price))
        catastral_dec = Decimal(str(req.catastral_value))

        # Calculate Retentions
        retentions = fiscal_engine.calculate_retentions(subtotal_dec, req.rfc_receptor)

        # Calculate ISAI
        isai = Decimal("0.00")
        if req.is_manzanillo:
            isai = fiscal_engine.calculate_isai(operation_price_dec, catastral_dec)

        return {
            "retentions": retentions,
            "isai_manzanillo": isai,
            "message": "Calculation successful"
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

class XMLGenerationRequest(BaseModel):
    invoice_data: Dict[str, Any]
    complemento_data: Dict[str, Any]

@app.post("/generate-xml")
def generate_xml_endpoint(req: XMLGenerationRequest):
    """
    Endpoint to generate and sign the CFDI 4.0 XML.
    Takes invoice data and complement data, applies fiscal logic, and returns XML.
    """
    try:
        # Validate Copropiedad if present
        adquirientes = req.complemento_data.get("adquirientes", [])
        if adquirientes:
            percentages = [Decimal(str(a.get("porcentaje", 0))) for a in adquirientes]
            if not fiscal_engine.validate_copropiedad(percentages):
                raise ValueError("La suma de porcentajes de copropiedad debe ser exactamente 100.00%")

        # Generate XML using the generator
        subtotal = Decimal(str(req.invoice_data.get("subtotal", 0)))
        rfc = req.invoice_data.get("receptor", {}).get("rfc", "")

        # Calculate retentions for reference or validation,
        # though generator applies them per concept now.
        retentions = fiscal_engine.calculate_retentions(subtotal, rfc)
        req.invoice_data["retentions"] = retentions

        cfdi = xml_generator.generar_xml(req.invoice_data, req.complemento_data)

        xml_str = cfdi.xml_bytes(encoding='utf-8').decode('utf-8')

        return {
            "xml": xml_str,
            "message": "XML generated successfully"
        }
    except ValueError as ve:
        raise HTTPException(status_code=400, detail=str(ve))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

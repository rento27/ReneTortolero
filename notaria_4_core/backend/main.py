from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from decimal import Decimal
from typing import List, Optional

from lib.fiscal_engine import calculate_isai, calculate_retentions, sanitize_name
from lib.xml_generator import generate_xml
# from lib.signer import CredentialLoader # Commented out until GCP env is ready

app = FastAPI(title="Notaria 4 Digital Core API", version="1.0.0")

class FiscalCalculationRequest(BaseModel):
    precio_operacion: Decimal
    valor_catastral: Decimal
    rfc_receptor: str
    subtotal_factura: Decimal

class FiscalCalculationResponse(BaseModel):
    isai_manzanillo: Decimal
    retenciones: dict

class DeedExtractionRequest(BaseModel):
    # In a real scenario this would accept a file upload,
    # but for JSON API testing we might pass a GCS URL
    document_url: str

class GenerateXMLRequest(BaseModel):
    rfc_receptor: str
    nombre_receptor: str
    regimen_receptor: str
    domicilio_receptor: str
    uso_cfdi: str
    conceptos: List[dict]
    folio: str

@app.get("/")
def health_check():
    return {"status": "ok", "service": "Notaria 4 Digital Core"}

@app.post("/calculate-fiscal", response_model=FiscalCalculationResponse)
def calculate_fiscal(request: FiscalCalculationRequest):
    """
    Calculates ISAI (Manzanillo) and Retentions (if Persona Moral).
    """
    isai = calculate_isai(request.precio_operacion, request.valor_catastral)
    retenciones = calculate_retentions(request.rfc_receptor, request.subtotal_factura)

    return {
        "isai_manzanillo": isai,
        "retenciones": retenciones
    }

@app.post("/extract-deed-data")
def extract_deed_data(request: DeedExtractionRequest):
    """
    Stub for OCR extraction.
    Phase 2 will implement Tesseract/SpaCy logic here.
    """
    return {
        "status": "simulated",
        "extracted_data": {
            "escritura": "23674",
            "volumen": "1540",
            "adquirente": "JUAN PEREZ",
            "monto": 1500000.00
        }
    }

@app.post("/generate-xml")
def generate_xml_endpoint(request: GenerateXMLRequest):
    """
    Generates an unsigned CFDI 4.0 XML structure.
    """
    try:
        # Mock Emisor (Notaria 4)
        emisor = {
            "Rfc": "TOSR520601AZ4",
            "Nombre": "RENE MANUEL TORTOLERO SANTILLANA",
            "RegimenFiscal": "612"
        }

        receptor = {
            "Rfc": request.rfc_receptor,
            "Nombre": request.nombre_receptor,
            "RegimenFiscal": request.regimen_receptor,
            "DomicilioFiscal": request.domicilio_receptor,
            "UsoCFDI": request.uso_cfdi
        }

        # Convert Pydantic/JSON concepts to dicts with Decimals if needed
        # satcfdi handles float/decimal, but strictness helps
        clean_conceptos = []
        for c in request.conceptos:
            clean_c = c.copy()
            clean_c['ValorUnitario'] = Decimal(str(c['ValorUnitario']))
            clean_c['Importe'] = Decimal(str(c['Importe']))
            clean_conceptos.append(clean_c)

        cfdi = generate_xml(
            emisor=emisor,
            receptor=receptor,
            conceptos=clean_conceptos,
            folio=request.folio
        )

        # In a real app we would return the signed XML string
        # Here we return the dict representation for verification
        return {"xml_data": cfdi.dump()}

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

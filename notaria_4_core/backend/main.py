from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional
from decimal import Decimal
import os

from lib import fiscal_engine, extraction_engine, xml_generator

app = FastAPI(title="Notaria 4 Digital Core API")

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Adjust in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class FiscalCalculationRequest(BaseModel):
    rfc_receptor: str
    subtotal: Decimal
    iva_trasladado: Decimal
    precio_operacion: Optional[Decimal] = None
    valor_catastral: Optional[Decimal] = None
    tasa_isai: Optional[Decimal] = Decimal("0.03")

class FiscalCalculationResponse(BaseModel):
    is_persona_moral: bool
    retentions: dict
    isai: Optional[Decimal] = None

@app.get("/")
async def root():
    return {"status": "ok", "service": "Notaria 4 Digital Core"}

@app.post("/calculate-fiscal", response_model=FiscalCalculationResponse)
async def calculate_fiscal(data: FiscalCalculationRequest):
    """
    Endpoint to calculate taxes (ISAI, Retention) based on input data.
    """
    # Calculate Retentions
    retention_result = fiscal_engine.calculate_retentions(
        data.rfc_receptor,
        data.subtotal,
        data.iva_trasladado
    )

    # Calculate ISAI if applicable
    isai_amount = None
    if data.precio_operacion and data.valor_catastral:
        isai_amount = fiscal_engine.calculate_isai_manzanillo(
            data.precio_operacion,
            data.valor_catastral,
            data.tasa_isai
        )

    return FiscalCalculationResponse(
        is_persona_moral=retention_result['is_persona_moral'],
        retentions={
            "isr": retention_result['isr_retention'],
            "iva": retention_result['iva_retention']
        },
        isai=isai_amount
    )

@app.post("/upload-deed")
async def upload_deed(file: UploadFile = File(...)):
    """
    Endpoint to upload a PDF deed, perform OCR/NLP, and extract data.
    """
    try:
        content = await file.read()

        # 1. Extract Text
        text = extraction_engine.extract_text_from_pdf(content)

        # 2. Extract Entities
        entities = extraction_engine.extract_entities(text)

        return {
            "filename": file.filename,
            "text_preview": text[:500],
            "extracted_data": entities
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/generate-cfdi")
async def generate_cfdi(data: dict):
    """
    Endpoint to generate the signed XML CFDI 4.0.
    """
    try:
        # Example: just demonstrating the connection.
        # In a real scenario, 'data' would be validated via Pydantic model
        # matching the complex CFDI structure.

        # 1. Generate Complemento
        complemento = xml_generator.generar_complemento_notarios(data.get("datos_notario", {}))

        # 2. Return the structure (or the signed XML string in production)
        return {
            "message": "CFDI Structure Generated",
            "complemento": complemento
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

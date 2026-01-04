from fastapi import FastAPI, UploadFile, File, HTTPException
from pydantic import BaseModel
from typing import List, Optional
from lib.fiscal_engine import FiscalEngine
from lib.xml_generator import XMLGenerator
import spacy
from decimal import Decimal

app = FastAPI(title="Notaría 4 Digital Core API")

# Load NLP model
try:
    nlp = spacy.load("es_core_news_lg")
except OSError:
    print("Warning: spacy model not found, using blank 'es'")
    nlp = spacy.blank("es")

class InvoiceItem(BaseModel):
    clave_prod_serv: str
    cantidad: float
    clave_unidad: str
    descripcion: str
    valor_unitario: float
    importe: float

class Receptor(BaseModel):
    rfc: str
    nombre: str
    cp: str
    regimen: str

class InvoiceRequest(BaseModel):
    subtotal: float
    items: List[InvoiceItem]
    receptor: Receptor

@app.get("/")
def read_root():
    return {"status": "active", "system": "Notaría 4 Digital Core"}

@app.post("/calculate-isai")
def calculate_isai(precio: float, valor_catastral: float):
    isai = FiscalEngine.calculate_isai_manzanillo(Decimal(str(precio)), Decimal(str(valor_catastral)))
    return {"isai_amount": float(isai)}

@app.post("/sanitize-name")
def sanitize_name(name: str):
    clean_name = FiscalEngine.sanitize_name(name)
    return {"original": name, "sanitized": clean_name}

@app.post("/generate-cfdi")
def generate_cfdi(request: InvoiceRequest):
    # This would normally load the signer from Secret Manager
    # For skeleton, we just mock the logic flow

    # Validate CP (Mocked for now as we don't have the catalog loaded)
    # real impl: if not FiscalEngine.validate_cp(request.receptor.cp): raise HTTPException...

    return {"status": "success", "message": "CFDI generation logic ready", "sanitized_receptor": FiscalEngine.sanitize_name(request.receptor.nombre)}

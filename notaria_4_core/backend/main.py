from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import List, Dict, Any, Optional
import base64
from lib.signer import SignerLoader
from lib.xml_generator import XMLGenerator

app = FastAPI(title="Notaria 4 Digital Core API")

# --- Pydantic Models ---

class Receptor(BaseModel):
    rfc: str
    razon_social: str
    uso_cfdi: str
    cp: str
    regimen_fiscal: str

class Concepto(BaseModel):
    clave_prod_serv: str
    cantidad: float
    clave_unidad: str
    descripcion: str
    valor_unitario: float
    importe: float
    objeto_imp: str

class InvoiceData(BaseModel):
    receptor: Receptor
    conceptos: List[Concepto]
    forma_pago: str = "03"
    metodo_pago: str = "PUE"

class Inmueble(BaseModel):
    tipo: str
    calle: str
    municipio: str
    estado: str
    cp: str

class Operacion(BaseModel):
    num_instrumento: str
    fecha_instrumento: str
    monto: float
    subtotal: float
    iva: float

class Notario(BaseModel):
    curp: str
    numero: int
    entidad: str
    adscripcion: str

class NotaryData(BaseModel):
    inmueble: Inmueble
    operacion: Operacion
    notario: Notario
    adquirientes: List[Dict[str, Any]] # Simplified for MVP

class CFDIRequest(BaseModel):
    invoice_data: InvoiceData
    notary_data: NotaryData

# --- Global Services ---
try:
    signer_loader = SignerLoader()
    signer = signer_loader.load_signer()
    xml_generator = XMLGenerator(signer)
except Exception as e:
    print(f"WARNING: Failed to initialize Signer: {e}")
    xml_generator = None

# --- Endpoints ---

@app.get("/")
async def root():
    """Root endpoint for basic verification."""
    return {"message": "Notaria 4 Digital Core API is running"}

@app.get("/health")
async def health_check():
    """Health check endpoint for Cloud Run."""
    return {"status": "healthy"}

@app.post("/api/v1/cfdi")
async def create_cfdi(request: CFDIRequest):
    """
    Generates and signs a CFDI 4.0 with Notaries Complement.
    """
    if not xml_generator:
        raise HTTPException(status_code=500, detail="XML Generator not initialized (Check Signer configuration)")

    try:
        # Pydantic -> Dict
        invoice_dict = request.invoice_data.dict()
        notary_dict = request.notary_data.dict()

        xml_bytes = xml_generator.generate_invoice(invoice_dict, notary_dict)

        # Return base64 encoded XML
        return {
            "xml_base64": base64.b64encode(xml_bytes).decode("utf-8"),
            "status": "signed"
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"CFDI Generation Error: {str(e)}")

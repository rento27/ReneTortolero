from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import List, Optional, Any
from decimal import Decimal
from datetime import date
from lib.fiscal_engine import sanitize_name, calculate_isai_manzanillo, calculate_retentions, validate_postal_code
from lib.xml_generator import generate_signed_xml

app = FastAPI(title="Notaria 4 Digital Core API", version="1.0.0")

class Receptor(BaseModel):
    rfc: str
    nombre: str
    uso_cfdi: str
    domicilio_fiscal: str

class Concepto(BaseModel):
    clave_prod_serv: str
    cantidad: Decimal
    clave_unidad: str
    descripcion: str
    valor_unitario: Decimal
    importe: Decimal
    objeto_imp: str

class Copropietario(BaseModel):
    nombre: str
    apellido_paterno: Optional[str] = None
    apellido_materno: Optional[str] = None
    rfc: str
    porcentaje: Decimal
    curp: Optional[str] = None

class Enajenante(BaseModel):
    nombre: str
    apellido_paterno: Optional[str] = None
    apellido_materno: Optional[str] = None
    rfc: str
    curp: str
    porcentaje: Optional[Decimal] = None
    es_copropiedad: bool = False

class Inmueble(BaseModel):
    tipo_inmueble: str # e.g. "03"
    calle: str
    no_exterior: str
    no_interior: Optional[str] = None
    codigo_postal: str
    colonia: Optional[str] = None
    municipio: str
    estado: str
    pais: str = "MEX"

class NotaryOperationData(BaseModel):
    num_instrumento: int
    fecha_inst_notarial: date
    monto_operacion: Decimal
    subtotal_operacion: Decimal
    iva_operacion: Optional[Decimal] = None
    enajenantes: List[Enajenante]
    inmuebles: List[Inmueble]

class InvoiceRequest(BaseModel):
    receptor: Receptor
    conceptos: List[Concepto]
    subtotal: Decimal
    total: Decimal
    copropietarios: Optional[List[Copropietario]] = None
    complemento_notarios: Optional[NotaryOperationData] = None
    datos_extra: Optional[dict] = None

class IsaiRequest(BaseModel):
    precio_operacion: Decimal
    valor_catastral: Decimal
    tasa: Optional[Decimal] = Decimal("0.03")

@app.get("/health")
def health_check():
    return {"status": "ok", "service": "notaria-4-core-backend"}

@app.post("/api/v1/calculate-isai")
def calculate_isai(request: IsaiRequest):
    try:
        isai = calculate_isai_manzanillo(request.precio_operacion, request.valor_catastral, request.tasa)
        return {
            "status": "success",
            "base_used": max(request.precio_operacion, request.valor_catastral),
            "isai_amount": isai
        }
    except Exception as e:
         raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/v1/cfdi")
def create_cfdi(request: InvoiceRequest):
    # Pydantic v2 compatibility
    data = request.model_dump()

    # 1. Sanitize Receptor Name
    data['receptor']['nombre'] = sanitize_name(data['receptor']['nombre'])

    # 1.1 Validate Postal Code
    # Assuming the API receives the 'domicilio_fiscal' as the CP code
    if not validate_postal_code(data['receptor']['domicilio_fiscal']):
         raise HTTPException(status_code=400, detail=f"Invalid Postal Code: {data['receptor']['domicilio_fiscal']}")

    # 2. Calculate Retentions (Logic Check)
    retentions = calculate_retentions(
        data['receptor']['rfc'],
        data['subtotal']
    )

    # 3. Generate XML
    try:
        # Pass the full data, including 'complemento_notarios' if present
        xml_bytes = generate_signed_xml(data)

        return {
            "status": "success",
            "xml_base64": xml_bytes.decode('utf-8'),
            "retentions_calculated": retentions
        }
    except ValueError as ve:
        raise HTTPException(status_code=400, detail=f"Validation Error: {str(ve)}")
    except Exception as e:
        # Log error in production
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/")
def root():
    return {"message": "Notaria 4 Digital Core API"}

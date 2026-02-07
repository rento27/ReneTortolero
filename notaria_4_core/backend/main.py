from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import List, Optional, Any
from decimal import Decimal
from lib.fiscal_engine import sanitize_name, calculate_isai_manzanillo, calculate_retentions, validate_postal_code
from lib.xml_generator import generate_signed_xml

app = FastAPI(title="Notaria 4 Digital Core API", version="1.0.0")

class Receptor(BaseModel):
    rfc: str
    nombre: str
    uso_cfdi: str
    domicilio_fiscal: str
    regimen_fiscal: str # Added for dynamic fiscal regime

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
    rfc: str
    porcentaje: Decimal

# --- Notarios Complement Models ---

class DatosNotarioModel(BaseModel):
    num_notaria: int = 4
    entidad_federativa: str = "06"
    adscripcion: str = "MANZANILLO COLIMA"
    curp: str # Notary CURP is mandatory

class DescInmuebleModel(BaseModel):
    tipo_inmueble: str
    calle: str
    no_exterior: Optional[str] = None
    no_interior: Optional[str] = None
    colonia: Optional[str] = None
    localidad: Optional[str] = None
    referencia: Optional[str] = None
    municipio: str
    estado: str
    pais: str
    codigo_postal: str

class DatosOperacionModel(BaseModel):
    num_instrumento_notarial: int
    fecha_inst_notarial: str # YYYY-MM-DD
    monto_operacion: Decimal
    subtotal: Decimal
    iva: Decimal

class DatosAdquirienteCopSCModel(BaseModel):
    nombre: str
    rfc: str
    porcentaje: Decimal
    apellido_paterno: Optional[str] = None
    apellido_materno: Optional[str] = None
    curp: Optional[str] = None

class DatosUnAdquirienteModel(BaseModel):
    nombre: str
    rfc: str
    apellido_paterno: Optional[str] = None
    apellido_materno: Optional[str] = None
    curp: Optional[str] = None

class DatosAdquirienteModel(BaseModel):
    copro_soc_conyugal_e: str # Si/No
    datos_un_adquiriente: Optional[DatosUnAdquirienteModel] = None
    datos_adquirientes_cop_sc: Optional[List[DatosAdquirienteCopSCModel]] = None

class DatosEnajenanteCopSCModel(BaseModel):
    nombre: str
    rfc: str
    porcentaje: Decimal
    apellido_paterno: Optional[str] = None
    apellido_materno: Optional[str] = None
    curp: Optional[str] = None

class DatosUnEnajenanteModel(BaseModel):
    nombre: str
    rfc: str
    apellido_paterno: Optional[str] = None
    apellido_materno: Optional[str] = None
    curp: Optional[str] = None

class DatosEnajenanteModel(BaseModel):
    copro_soc_conyugal_e: str # Si/No
    datos_un_enajenante: Optional[DatosUnEnajenanteModel] = None
    datos_enajenantes_cop_sc: Optional[List[DatosEnajenanteCopSCModel]] = None

class ComplementoNotariosModel(BaseModel):
    datos_notario: Optional[DatosNotarioModel] = None
    desc_inmuebles: List[DescInmuebleModel]
    datos_operacion: DatosOperacionModel
    datos_adquiriente: DatosAdquirienteModel
    datos_enajenante: DatosEnajenanteModel

# ----------------------------------

class InvoiceRequest(BaseModel):
    receptor: Receptor
    conceptos: List[Concepto]
    subtotal: Decimal
    total: Decimal
    copropietarios: Optional[List[Copropietario]] = None
    complemento_notarios: Optional[ComplementoNotariosModel] = None
    datos_extra: Optional[dict] = None

@app.get("/health")
def health_check():
    return {"status": "ok", "service": "notaria-4-core-backend"}

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
        xml_bytes = generate_signed_xml(data)
        # In a real scenario, we might upload this to storage and return a URL
        # For now, return the stub content
        return {
            "status": "success",
            "xml_base64": xml_bytes.decode('utf-8'), # Stub returns simple string bytes
            "retentions_calculated": retentions
        }
    except ValueError as ve:
        raise HTTPException(status_code=400, detail=f"Validation Error: {str(ve)}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/")
def root():
    return {"message": "Notaria 4 Digital Core API"}

from pydantic import BaseModel, Field, validator
from typing import List, Optional
from decimal import Decimal
from datetime import date

# --- Notarios Publicos Complement Models ---

class DatosNotarioModel(BaseModel):
    # Optional fields as they can be hardcoded or inferred
    num_notaria: int = 4
    entidad_federativa: str = "06"
    adscripcion: str = "MANZANILLO COLIMA"
    curp: Optional[str] = None

class DatosOperacionModel(BaseModel):
    num_instrumento_notarial: int
    fecha_inst_notarial: date
    monto_operacion: Decimal
    subtotal: Decimal
    iva: Decimal

class DescInmuebleModel(BaseModel):
    tipo_inmueble: str # Catalog 01, 02, 03...
    calle: str
    no_exterior: Optional[str] = None
    no_interior: Optional[str] = None
    colonia: Optional[str] = None
    localidad: Optional[str] = None
    referencia: Optional[str] = None
    municipio: str
    estado: str
    pais: str = "MEX"
    codigo_postal: str

class DatosAdquirienteModel(BaseModel):
    nombre: str
    apellido_paterno: Optional[str] = None
    apellido_materno: Optional[str] = None
    rfc: str
    curp: Optional[str] = None
    copro_soc_conyugal_e: str # "Si" or "No"
    porcentaje: Optional[Decimal] = None

class DatosEnajenanteModel(BaseModel):
    nombre: str
    apellido_paterno: Optional[str] = None
    apellido_materno: Optional[str] = None
    rfc: str
    curp: Optional[str] = None
    copro_soc_conyugal_e: str # "Si" or "No"
    porcentaje: Optional[Decimal] = None

class ComplementoNotariosModel(BaseModel):
    datos_notario: Optional[DatosNotarioModel] = None
    datos_operacion: DatosOperacionModel
    inmuebles: List[DescInmuebleModel]
    adquirientes: List[DatosAdquirienteModel]
    enajenantes: List[DatosEnajenanteModel]

# --- Main Invoice Models ---

class Receptor(BaseModel):
    rfc: str
    nombre: str
    uso_cfdi: str
    domicilio_fiscal: str
    regimen_fiscal: Optional[str] = None

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

class InvoiceRequest(BaseModel):
    receptor: Receptor
    conceptos: List[Concepto]
    subtotal: Decimal
    total: Decimal
    copropietarios: Optional[List[Copropietario]] = None
    complemento_notarios: Optional[ComplementoNotariosModel] = None
    datos_extra: Optional[dict] = None

class ISAIRequest(BaseModel):
    precio_operacion: Decimal
    valor_catastral: Decimal
    tasa: Optional[Decimal] = None

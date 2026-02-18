from pydantic import BaseModel, Field
from typing import List, Optional
from decimal import Decimal
from datetime import date

class Receptor(BaseModel):
    rfc: str
    nombre: str
    uso_cfdi: str
    domicilio_fiscal: str
    regimen_fiscal: Optional[str] = None # Added for flexibility

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

# --- Complemento Notarios Models ---

class DatosNotario(BaseModel):
    curp: str
    num_notaria: int
    entidad_federativa: str
    adscripcion: Optional[str] = None

class DatosOperacion(BaseModel):
    num_instrumento_notarial: int
    fecha_inst_notarial: date
    monto_operacion: Decimal
    subtotal: Decimal
    iva: Decimal

class DescInmueble(BaseModel):
    tipo_inmueble: str
    calle: str
    no_exterior: Optional[str] = None
    no_interior: Optional[str] = None
    colonia: Optional[str] = None
    localidad: Optional[str] = None
    municipio: str
    estado: str
    pais: str
    codigo_postal: str

class DatosAdquiriente(BaseModel):
    nombre: str
    rfc: Optional[str] = None
    curp: Optional[str] = None
    copro_soc_conyugal_e: str # "Si" or "No"
    porcentaje: Optional[Decimal] = None
    apellido_paterno: Optional[str] = None # Added for structured name support
    apellido_materno: Optional[str] = None

class DatosEnajenante(BaseModel):
    nombre: str
    rfc: Optional[str] = None
    curp: Optional[str] = None
    copro_soc_conyugal_e: str # "Si" or "No"
    porcentaje: Optional[Decimal] = None
    apellido_paterno: Optional[str] = None
    apellido_materno: Optional[str] = None

class ComplementoNotariosModel(BaseModel):
    datos_notario: Optional[DatosNotario] = None # Optional because some fields might be hardcoded in backend
    datos_operacion: DatosOperacion
    desc_inmuebles: List[DescInmueble]
    datos_adquirientes: List[DatosAdquiriente]
    datos_enajenantes: Optional[List[DatosEnajenante]] = None

# --- Request Models ---

class InvoiceRequest(BaseModel):
    receptor: Receptor
    conceptos: List[Concepto]
    subtotal: Decimal
    total: Decimal
    copropietarios: Optional[List[Copropietario]] = None
    datos_extra: Optional[dict] = None
    complemento_notarios: Optional[ComplementoNotariosModel] = None

class ISAIRequest(BaseModel):
    precio_operacion: Decimal
    valor_catastral: Decimal
    tasa: Optional[Decimal] = Decimal("0.03")

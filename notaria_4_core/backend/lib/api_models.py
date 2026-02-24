from pydantic import BaseModel, Field
from typing import List, Optional, Any
from decimal import Decimal
from datetime import date

# --- CFDI Core Models ---

class Receptor(BaseModel):
    rfc: str
    nombre: str
    uso_cfdi: str
    domicilio_fiscal: str
    regimen_fiscal: str  # Added for CFDI 4.0 validation

class Concepto(BaseModel):
    clave_prod_serv: str
    cantidad: Decimal
    clave_unidad: str
    descripcion: str
    valor_unitario: Decimal
    importe: Decimal
    objeto_imp: str
    impuestos: Optional[dict] = None  # To support manual tax passing if needed

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
    referencia: Optional[str] = None
    municipio: Optional[str] = None
    estado: str
    pais: str
    codigo_postal: str

class DatosAdquiriente(BaseModel):
    nombre: str
    rfc: Optional[str] = None
    curp: Optional[str] = None
    porcentaje: Optional[Decimal] = None
    copro_soc_conyugal_e: str = Field(..., pattern="^(Si|No)$")
    apellido_paterno: Optional[str] = None
    apellido_materno: Optional[str] = None

class DatosEnajenante(BaseModel):
    nombre: str
    rfc: Optional[str] = None
    curp: Optional[str] = None
    porcentaje: Optional[Decimal] = None
    copro_soc_conyugal_e: str = Field(..., pattern="^(Si|No)$")
    apellido_paterno: Optional[str] = None
    apellido_materno: Optional[str] = None

class ComplementoNotariosModel(BaseModel):
    datos_notario: DatosNotario
    datos_operacion: DatosOperacion
    desc_inmuebles: List[DescInmueble]
    datos_adquirientes: List[DatosAdquiriente]
    datos_enajenantes: List[DatosEnajenante]

# --- Main Request Model ---

class InvoiceRequest(BaseModel):
    receptor: Receptor
    conceptos: List[Concepto]
    subtotal: Decimal
    total: Decimal
    complemento_notarios: Optional[ComplementoNotariosModel] = None
    datos_extra: Optional[dict] = None

class ISAIRequest(BaseModel):
    precio_operacion: Decimal
    valor_catastral: Decimal
    tasa: Optional[Decimal] = None

from typing import List, Optional
from decimal import Decimal
from pydantic import BaseModel, Field
from datetime import date

# --- Basic CFDI Models ---

class Receptor(BaseModel):
    rfc: str
    nombre: str
    uso_cfdi: str
    domicilio_fiscal: str
    regimen_fiscal: Optional[str] = "616"  # Default for Sin Obligaciones Fiscales or specific logic

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

# --- Complemento Notarios Publicos Models ---

class DatosNotarioModel(BaseModel):
    curp_notario: str = "TOSR520601HOCMXA00" # Fallback/Default
    num_notaria: int = 4
    entidad_federativa: str = "06"
    adscripcion: str = "MANZANILLO COLIMA"

class DatosOperacionModel(BaseModel):
    num_instrumento_notarial: int
    fecha_inst_notarial: date
    monto_operacion: Decimal
    subtotal: Decimal
    iva: Decimal

class DescInmuebleModel(BaseModel):
    tipo_inmueble: str
    calle: str
    no_exterior: Optional[str] = None
    no_interior: Optional[str] = None
    colonia: Optional[str] = None
    localidad: Optional[str] = None
    municipio: Optional[str] = None
    entidad_federativa: str
    pais: str
    codigo_postal: str

class DatosAdquirienteModel(BaseModel):
    nombre: str
    apellido_paterno: Optional[str] = None
    apellido_materno: Optional[str] = None
    rfc: str
    curp: str
    porcentaje: Optional[Decimal] = None # For coproperty validation
    copro_soc_conyugal_e: str = "No"

class DatosEnajenanteModel(BaseModel):
    nombre: str
    apellido_paterno: Optional[str] = None
    apellido_materno: Optional[str] = None
    rfc: str
    curp: str
    porcentaje: Optional[Decimal] = None # For coproperty validation
    copro_soc_conyugal_e: str = "No"

class ComplementoNotariosModel(BaseModel):
    datos_operacion: DatosOperacionModel
    desc_inmuebles: List[DescInmuebleModel]
    datos_adquirientes: List[DatosAdquirienteModel]
    datos_enajenantes: List[DatosEnajenanteModel]
    datos_notario: Optional[DatosNotarioModel] = Field(default_factory=DatosNotarioModel)

# --- Main Request Model ---

class InvoiceRequest(BaseModel):
    receptor: Receptor
    conceptos: List[Concepto]
    subtotal: Decimal
    total: Decimal
    # Deprecated: copropietarios (use complement data)
    copropietarios: Optional[List[Copropietario]] = None
    complemento_notarios: Optional[ComplementoNotariosModel] = None
    datos_extra: Optional[dict] = None

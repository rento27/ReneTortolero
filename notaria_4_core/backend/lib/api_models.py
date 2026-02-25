from pydantic import BaseModel, Field
from typing import List, Optional, Literal
from decimal import Decimal
from datetime import date

# --- Complemento Notarios Models ---

class DatosNotario(BaseModel):
    curp: str = Field(..., max_length=18, min_length=18)
    num_notaria: int = 4
    entidad_federativa: str = "06"
    adscripcion: str = "MANZANILLO, COLIMA" # Hardcoded per requirement

class DatosOperacion(BaseModel):
    num_instrumento_notarial: int
    fecha_inst_notarial: date
    monto_operacion: Decimal
    subtotal: Decimal
    iva: Decimal

class DescInmueble(BaseModel):
    tipo_inmueble: str # Catalog c_TipoInmueble
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

class DatosEnajenante(BaseModel):
    nombre: str
    apellido_paterno: Optional[str] = None # Logic to split name if not provided
    apellido_materno: Optional[str] = None
    rfc: str
    curp: str
    porcentaje: Optional[Decimal] = None # Required for copropiedad
    copro_soc_conyugal_e: Literal["Si", "No"] = "No"

class DatosAdquiriente(BaseModel):
    nombre: str
    apellido_paterno: Optional[str] = None
    apellido_materno: Optional[str] = None
    rfc: str
    curp: Optional[str] = None
    porcentaje: Optional[Decimal] = None
    copro_soc_conyugal_e: Literal["Si", "No"] = "No"

class ComplementoNotariosModel(BaseModel):
    datos_notario: Optional[DatosNotario] = None # Optional, can be defaulted
    datos_operacion: DatosOperacion
    desc_inmuebles: List[DescInmueble]
    datos_enajenantes: List[DatosEnajenante]
    datos_adquirientes: List[DatosAdquiriente]

# --- CFDI Models ---

class Receptor(BaseModel):
    rfc: str
    nombre: str
    uso_cfdi: str
    domicilio_fiscal: str
    regimen_fiscal: str # Added based on requirements (e.g., 601, 616)

class Concepto(BaseModel):
    clave_prod_serv: str
    cantidad: Decimal
    clave_unidad: str
    descripcion: str
    valor_unitario: Decimal
    importe: Decimal
    objeto_imp: str

class InvoiceRequest(BaseModel):
    receptor: Receptor
    conceptos: List[Concepto]
    subtotal: Decimal
    total: Decimal
    complemento_notarios: Optional[ComplementoNotariosModel] = None
    datos_extra: Optional[dict] = None

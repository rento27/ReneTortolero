from pydantic import BaseModel, Field, validator
from typing import List, Optional, Literal
from decimal import Decimal
from datetime import date

# --- CFDI Base Models ---

class Receptor(BaseModel):
    rfc: str = Field(..., min_length=12, max_length=13)
    nombre: str
    uso_cfdi: str
    domicilio_fiscal: str = Field(..., min_length=5, max_length=5)
    regimen_fiscal: str

class Concepto(BaseModel):
    clave_prod_serv: str
    no_identificacion: Optional[str] = None
    cantidad: Decimal
    clave_unidad: str
    unidad: Optional[str] = None
    descripcion: str
    valor_unitario: Decimal
    importe: Decimal # Though satcfdi calculates, we might validate it matches
    objeto_imp: str # '01', '02', etc.
    descuento: Optional[Decimal] = None

# --- Complemento Notarios Models ---

class DatosNotario(BaseModel):
    curp: Optional[str] =Field(None, min_length=18, max_length=18)
    num_notaria: int
    entidad_federativa: str
    adscripcion: Optional[str] = None

class DatosInmueble(BaseModel):
    tipo_inmueble: str # catalog c_TipoInmueble
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

class DatosAdquiriente(BaseModel):
    nombre: str
    apellido_paterno: Optional[str] = None
    apellido_materno: Optional[str] = None
    rfc: str = Field(..., min_length=12, max_length=13)
    curp: Optional[str] = Field(None, min_length=18, max_length=18)
    porcentaje: Decimal = Field(..., ge=0, le=100)
    copro_soc_conyugal_e: Literal['Si', 'No'] = 'No'

class DatosEnajenante(BaseModel):
    nombre: str
    apellido_paterno: Optional[str] = None
    apellido_materno: Optional[str] = None
    rfc: str = Field(..., min_length=12, max_length=13)
    curp: str = Field(..., min_length=18, max_length=18) # Mandatory for Enajenante
    porcentaje: Decimal = Field(..., ge=0, le=100)
    copro_soc_conyugal_e: Literal['Si', 'No'] = 'No'

class DatosOperacion(BaseModel):
    num_instrumento_notarial: int
    fecha_inst_notarial: date
    monto_operacion: Decimal
    subtotal: Decimal
    iva: Decimal

class ComplementoNotariosModel(BaseModel):
    datos_notario: DatosNotario
    datos_operacion: DatosOperacion
    datos_inmueble: DatosInmueble
    datos_adquirientes: List[DatosAdquiriente]
    datos_enajenantes: List[DatosEnajenante]

# --- Main Request Model ---

class InvoiceRequest(BaseModel):
    receptor: Receptor
    conceptos: List[Concepto]
    # Subtotal and Total are calculated by satcfdi, but we might receive them for validation or simple pass-through logic checks
    subtotal: Optional[Decimal] = None
    total: Optional[Decimal] = None
    forma_pago: str = '99'
    metodo_pago: str = 'PPD'
    serie: Optional[str] = None
    folio: Optional[str] = None
    complemento_notarios: Optional[ComplementoNotariosModel] = None

class ISAIRequest(BaseModel):
    valor_operacion: Decimal
    valor_catastral: Decimal
    tasa: Optional[Decimal] = Decimal("0.03")

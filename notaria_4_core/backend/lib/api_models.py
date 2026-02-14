from pydantic import BaseModel, Field, validator
from typing import List, Optional
from decimal import Decimal
from datetime import date

# --- Basic Invoice Models ---

class Receptor(BaseModel):
    rfc: str = Field(..., min_length=12, max_length=13, pattern=r"^[A-Z&Ñ]{3,4}\d{6}[A-Z0-9]{3}$")
    nombre: str
    uso_cfdi: str
    domicilio_fiscal: str
    regimen_fiscal: Optional[str] = Field(default="601", description="Fiscal Regime")

class Concepto(BaseModel):
    clave_prod_serv: str
    cantidad: Decimal
    clave_unidad: str
    descripcion: str
    valor_unitario: Decimal
    importe: Decimal
    objeto_imp: str
    # Optional field for specific taxes if needed, but logic currently handles it via fiscal engine

# --- Complemento Notarios Models ---

class DatosNotario(BaseModel):
    num_notaria: int = Field(default=4)
    entidad_federativa: str = Field(default="06") # Colima
    adscripcion: str = Field(default="MANZANILLO COLIMA")
    curp: Optional[str] = Field(None, min_length=18, max_length=18)

class DatosOperacion(BaseModel):
    num_instrumento_notarial: int
    fecha_inst_notarial: date
    monto_operacion: Decimal
    subtotal: Decimal
    iva: Decimal

class DescInmueble(BaseModel):
    tipo_inmueble: str # catalog c_TipoInmueble
    calle: str
    no_exterior: Optional[str] = None
    no_interior: Optional[str] = None
    colonia: Optional[str] = None
    localidad: Optional[str] = None
    referencia: Optional[str] = None
    municipio: str
    estado: str
    pais: str = Field(default="MEX")
    codigo_postal: str

class DatosAdquiriente(BaseModel):
    nombre: str
    apellido_paterno: Optional[str] = None # Optional because logic might split full name
    apellido_materno: Optional[str] = None
    rfc: Optional[str] = None
    curp: Optional[str] = None
    porcentaje: Optional[Decimal] = None # Required if coproperty
    copro_soc_conyugal_e: str = Field(default="No", pattern="^(Si|No)$")

class DatosEnajenante(BaseModel):
    nombre: str
    apellido_paterno: Optional[str] = None
    apellido_materno: Optional[str] = None
    rfc: Optional[str] = None
    curp: Optional[str] = None
    porcentaje: Optional[Decimal] = None
    copro_soc_conyugal_e: str = Field(default="No", pattern="^(Si|No)$")

class ComplementoNotariosModel(BaseModel):
    datos_notario: Optional[DatosNotario] = Field(default_factory=DatosNotario)
    datos_operacion: DatosOperacion
    desc_inmuebles: List[DescInmueble]
    datos_adquirientes: List[DatosAdquiriente]
    datos_enajenantes: List[DatosEnajenante]

# --- Main Request Model ---

class Copropietario(BaseModel):
    # This might be redundant if using ComplementoNotariosModel,
    # but keeping for backward compatibility or simple invoices
    nombre: str
    rfc: str
    porcentaje: Decimal

class InvoiceRequest(BaseModel):
    receptor: Receptor
    conceptos: List[Concepto]
    subtotal: Decimal
    total: Decimal
    copropietarios: Optional[List[Copropietario]] = None
    datos_extra: Optional[dict] = None
    complemento_notarios: Optional[ComplementoNotariosModel] = None

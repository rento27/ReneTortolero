from pydantic import BaseModel, Field
from typing import List, Optional
from decimal import Decimal
from datetime import date

# --- Basic Invoice Models ---

class Receptor(BaseModel):
    rfc: str
    nombre: str
    uso_cfdi: str
    domicilio_fiscal: str
    regimen_fiscal: Optional[str] = "601" # Default or passed explicitly

class Concepto(BaseModel):
    clave_prod_serv: str
    cantidad: Decimal
    clave_unidad: str
    descripcion: str
    valor_unitario: Decimal
    importe: Decimal
    objeto_imp: str

class Copropietario(BaseModel):
    # This might be redundant if we use ComplementoNotariosModel,
    # but keeping it for backward compatibility if needed.
    nombre: str
    rfc: str
    porcentaje: Decimal

# --- Complemento Notarios Models ---

class Inmueble(BaseModel):
    tipo_inmueble: str
    calle: str
    no_exterior: Optional[str] = None
    no_interior: Optional[str] = None
    colonia: Optional[str] = None
    localidad: Optional[str] = None
    referencia: Optional[str] = None
    municipio: str
    entidad_federativa: str
    pais: str
    codigo_postal: str

class DatosAdquiriente(BaseModel):
    nombre: str
    apellido_paterno: Optional[str] = None
    apellido_materno: Optional[str] = None
    rfc: Optional[str] = None # Optional if foreign?
    curp: Optional[str] = None
    porcentaje: Optional[Decimal] = None # Required if coproperty
    copro_soc_conyugal_e: str = "No" # "Si" or "No"

class DatosEnajenante(BaseModel):
    nombre: str
    apellido_paterno: Optional[str] = None
    apellido_materno: Optional[str] = None
    rfc: Optional[str] = None
    curp: Optional[str] = None
    porcentaje: Optional[Decimal] = None
    copro_soc_conyugal_e: str = "No"

class DatosNotario(BaseModel):
    curp: Optional[str] = None # Defaults can be handled in logic
    num_notaria: int = 4
    entidad_federativa: str = "06" # Colima
    adscripcion: str = "MANZANILLO, COLIMA"

class DatosOperacion(BaseModel):
    num_instrumento_notarial: int
    fecha_inst_notarial: date
    monto_operacion: Decimal
    subtotal: Decimal
    iva: Decimal

class ComplementoNotariosModel(BaseModel):
    datos_operacion: DatosOperacion
    datos_notario: Optional[DatosNotario] = None # Optional, can use defaults
    inmueble: Inmueble
    adquirientes: List[DatosAdquiriente]
    enajenantes: List[DatosEnajenante]

# --- Main Request Model ---

class InvoiceRequest(BaseModel):
    receptor: Receptor
    conceptos: List[Concepto]
    subtotal: Decimal
    total: Decimal
    copropietarios: Optional[List[Copropietario]] = None
    datos_extra: Optional[dict] = None
    complemento_notarios: Optional[ComplementoNotariosModel] = None

from pydantic import BaseModel, Field
from typing import List, Optional, Union
from decimal import Decimal
from datetime import date

# Regex Patterns
RFC_REGEX = r"^[A-Z&Ñ]{3,4}\d{6}[A-Z0-9]{3}$"
CP_REGEX = r"^\d{5}$"

class Receptor(BaseModel):
    rfc: str = Field(..., pattern=RFC_REGEX)
    nombre: str
    uso_cfdi: str
    domicilio_fiscal: str = Field(..., pattern=CP_REGEX)
    regimen_fiscal: str

class Concepto(BaseModel):
    clave_prod_serv: str
    cantidad: Decimal
    clave_unidad: str
    descripcion: str
    valor_unitario: Decimal
    importe: Decimal
    objeto_imp: str

# --- Complemento Notarios Models ---

class DatosNotario(BaseModel):
    num_notaria: int
    entidad_federativa: str
    adscripcion: str
    curp: Optional[str] = None

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
    municipio: str
    estado: str
    pais: str
    codigo_postal: str

# Adquirientes
class DatosUnAdquiriente(BaseModel):
    nombre: str
    apellido_paterno: Optional[str] = None
    apellido_materno: Optional[str] = None
    rfc: str
    curp: Optional[str] = None

class DatosAdquirienteCopSC(BaseModel):
    nombre: str
    apellido_paterno: Optional[str] = None
    apellido_materno: Optional[str] = None
    rfc: str
    curp: Optional[str] = None
    porcentaje: Decimal

class DatosAdquiriente(BaseModel):
    copro_soc_conyugal_e: str
    datos_un_adquiriente: Optional[DatosUnAdquiriente] = None
    datos_adquirientes_cop_sc: Optional[List[DatosAdquirienteCopSC]] = None

# Enajenantes
class DatosUnEnajenante(BaseModel):
    nombre: str
    apellido_paterno: Optional[str] = None
    apellido_materno: Optional[str] = None
    rfc: str
    curp: str # Mandatory

class DatosEnajenanteCopSC(BaseModel):
    nombre: str
    apellido_paterno: Optional[str] = None
    apellido_materno: Optional[str] = None
    rfc: str
    curp: str # Mandatory
    porcentaje: Decimal

class DatosEnajenante(BaseModel):
    copro_soc_conyugal_e: str
    datos_un_enajenante: Optional[DatosUnEnajenante] = None
    datos_enajenantes_cop_sc: Optional[List[DatosEnajenanteCopSC]] = None

class ComplementoNotariosModel(BaseModel):
    datos_notario: DatosNotario
    datos_operacion: DatosOperacion
    desc_inmuebles: List[DescInmueble]
    datos_adquiriente: DatosAdquiriente
    datos_enajenante: Optional[DatosEnajenante] = None

class InvoiceRequest(BaseModel):
    receptor: Receptor
    conceptos: List[Concepto]
    subtotal: Decimal
    total: Decimal
    complemento_notarios: Optional[ComplementoNotariosModel] = None
    datos_extra: Optional[dict] = None

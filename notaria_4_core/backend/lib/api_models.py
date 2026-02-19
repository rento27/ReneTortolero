from pydantic import BaseModel, Field
from typing import List, Optional
from decimal import Decimal
from datetime import date

class Receptor(BaseModel):
    rfc: str
    nombre: str
    uso_cfdi: str
    domicilio_fiscal: str
    regimen_fiscal: Optional[str] = "601"

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

class DatosNotarioModel(BaseModel):
    curp: Optional[str] = None # Can be defaulted if not provided
    num_notaria: Optional[int] = 4
    entidad_federativa: Optional[str] = "06"
    adscripcion: Optional[str] = "MANZANILLO, COLIMA"

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
    referencia: Optional[str] = None
    municipio: str
    estado: str
    pais: str
    codigo_postal: str

class DatosAdquirienteModel(BaseModel):
    nombre: str
    apellido_paterno: Optional[str] = None
    apellido_materno: Optional[str] = None
    rfc: Optional[str] = None
    curp: Optional[str] = None
    porcentaje: Optional[Decimal] = None
    copro_soc_conyugal_e: Optional[str] = "No"

class DatosEnajenanteModel(BaseModel):
    nombre: str
    apellido_paterno: Optional[str] = None
    apellido_materno: Optional[str] = None
    rfc: Optional[str] = None
    curp: Optional[str] = None
    porcentaje: Optional[Decimal] = None
    copro_soc_conyugal_e: Optional[str] = "No"

class ComplementoNotariosModel(BaseModel):
    datos_notario: Optional[DatosNotarioModel] = None
    datos_operacion: DatosOperacionModel
    desc_inmuebles: List[DescInmuebleModel]
    datos_adquirientes: List[DatosAdquirienteModel]
    datos_enajenantes: Optional[List[DatosEnajenanteModel]] = []

# --- Main Request Model ---

class InvoiceRequest(BaseModel):
    receptor: Receptor
    conceptos: List[Concepto]
    subtotal: Decimal
    total: Decimal
    copropietarios: Optional[List[Copropietario]] = None
    datos_extra: Optional[dict] = None
    complemento_notarios: Optional[ComplementoNotariosModel] = None

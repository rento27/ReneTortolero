from pydantic import BaseModel, Field
from typing import List, Optional
from decimal import Decimal

class Receptor(BaseModel):
    rfc: str
    nombre: str
    uso_cfdi: str
    domicilio_fiscal: str
    regimen_fiscal: Optional[str] = '601' # From memory: includes a `regimen_fiscal` field to support dynamic fiscal regime assignment

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

class DatosAdquiriente(BaseModel):
    # From memory: includes optional apellido_paterno and apellido_materno fields
    nombre: str
    apellido_paterno: Optional[str] = None
    apellido_materno: Optional[str] = None
    rfc: str
    curp: Optional[str] = None
    copro_soc_conyugal_e: str

class DatosEnajenante(BaseModel):
    nombre: str
    apellido_paterno: Optional[str] = None
    apellido_materno: Optional[str] = None
    rfc: str
    curp: str # Mandatory for Enajenante in XML schema
    copro_soc_conyugal_e: str

class DescInmueble(BaseModel):
    tipo_inmueble: str
    calle: str
    no_exterior: Optional[str] = None
    no_interior: Optional[str] = None
    colonia: Optional[str] = None
    localidad: Optional[str] = None
    referencia: Optional[str] = None
    municipio: str
    estado: str # DescInmueble class uses the argument estado for the state
    pais: str
    codigo_postal: str

class DatosNotario(BaseModel):
    curp: str = Field(min_length=18, max_length=18)
    num_notaria: int = 4
    entidad_federativa: str = "06"
    adscripcion: str = "MANZANILLO COLIMA"

class DatosOperacion(BaseModel):
    num_instrumento_notarial: int
    fecha_inst_notarial: str
    monto_operacion: Decimal
    subtotal: Decimal
    iva: Decimal

class ComplementoNotariosModel(BaseModel):
    datos_notario: Optional[DatosNotario] = None
    datos_operacion: DatosOperacion
    datos_enajenante: List[DatosEnajenante]
    datos_adquiriente: List[DatosAdquiriente]
    desc_inmuebles: List[DescInmueble]

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

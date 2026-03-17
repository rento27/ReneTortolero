from pydantic import BaseModel, Field, field_validator
from typing import List, Optional
from decimal import Decimal
import datetime

class Receptor(BaseModel):
    rfc: str
    nombre: str
    uso_cfdi: str
    domicilio_fiscal: str

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

class InvoiceRequest(BaseModel):
    receptor: Receptor
    conceptos: List[Concepto]
    subtotal: Decimal
    total: Decimal
    copropietarios: Optional[List[Copropietario]] = None
    datos_extra: Optional[dict] = None
    complemento_notarios: Optional['ComplementoNotariosModel'] = None

class ISAIRequest(BaseModel):
    operation_price: Decimal
    cadastral_value: Decimal

class DescInmueble(BaseModel):
    tipo_inmueble: str
    calle: str
    estado: str
    codigo_postal: str

class DatosAdquiriente(BaseModel):
    copro_soc_conyugal_e: str
    rfc: str
    nombre: str
    apellido_paterno: Optional[str] = None
    apellido_materno: Optional[str] = None
    porcentaje: Optional[Decimal] = None
    curp: Optional[str] = None

class DatosEnajenante(BaseModel):
    copro_soc_conyugal_e: str
    rfc: str
    nombre: str
    apellido_paterno: Optional[str] = None
    apellido_materno: Optional[str] = None
    porcentaje: Optional[Decimal] = None
    curp: str

class DatosNotario(BaseModel):
    curp: str = Field(default="TOSR520601HOCMXA00")
    num_notaria: int = 4
    entidad_federativa: str = "06"
    adscripcion: str = "MANZANILLO COLIMA"

class DatosOperacion(BaseModel):
    num_instrumento_notarial: str
    fecha_inst_notarial: str
    monto_operacion: Decimal
    subtotal: Decimal
    iva: Decimal

class ComplementoNotariosModel(BaseModel):
    desc_inmuebles: List[DescInmueble]
    datos_operacion: DatosOperacion
    datos_notario: Optional[DatosNotario] = None
    datos_adquiriente: List[DatosAdquiriente]
    datos_enajenante: List[DatosEnajenante]

    def __init__(self, **data):
        if 'datos_notario' not in data or not data['datos_notario']:
            data['datos_notario'] = DatosNotario().model_dump()
        super().__init__(**data)

InvoiceRequest.model_rebuild()

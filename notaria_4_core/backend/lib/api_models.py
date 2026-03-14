from pydantic import BaseModel, Field
from typing import List, Optional
from decimal import Decimal

class Receptor(BaseModel):
    rfc: str
    nombre: str
    uso_cfdi: str
    domicilio_fiscal: str
    regimen_fiscal: str

class Concepto(BaseModel):
    clave_prod_serv: str
    cantidad: Decimal
    clave_unidad: str
    descripcion: str
    valor_unitario: Decimal
    objeto_imp: str

class Copropietario(BaseModel):
    nombre: str
    rfc: str
    porcentaje: Decimal

class DatosAdquiriente(BaseModel):
    nombre: str
    apellido_paterno: Optional[str] = None
    apellido_materno: Optional[str] = None
    rfc: str
    curp: Optional[str] = None
    copro_soc_conyugal_e: str
    porcentaje: Optional[Decimal] = None

class DatosEnajenante(BaseModel):
    nombre: str
    apellido_paterno: Optional[str] = None
    apellido_materno: Optional[str] = None
    rfc: str
    curp: str
    copro_soc_conyugal_e: str
    porcentaje: Optional[Decimal] = None

class DatosNotario(BaseModel):
    curp: str = Field(default='TOSR520601HOCMXA00')

class DatosOperacion(BaseModel):
    num_instrumento_notarial: int
    fecha_inst_notarial: str
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

class ComplementoNotariosModel(BaseModel):
    datos_operacion: DatosOperacion
    datos_notario: Optional[DatosNotario] = Field(default_factory=DatosNotario)
    datos_enajenante: List[DatosEnajenante]
    datos_adquiriente: List[DatosAdquiriente]
    desc_inmuebles: List[DescInmueble]

class InvoiceRequest(BaseModel):
    receptor: Receptor
    conceptos: List[Concepto]
    copropietarios: Optional[List[Copropietario]] = None
    complemento_notarios: Optional[ComplementoNotariosModel] = None
    datos_extra: Optional[dict] = None

class ISAIRequest(BaseModel):
    operation_price: Decimal
    cadastral_value: Decimal

from pydantic import BaseModel, Field
from typing import List, Optional
from decimal import Decimal

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

class DatosAdquiriente(BaseModel):
    nombre: str
    apellido_paterno: Optional[str] = None
    apellido_materno: Optional[str] = None
    rfc: str
    curp: str
    porcentaje: Optional[Decimal] = None
    copro_soc_conyugal_e: str

class DatosEnajenante(BaseModel):
    nombre: str
    apellido_paterno: Optional[str] = None
    apellido_materno: Optional[str] = None
    rfc: str
    curp: str
    porcentaje: Optional[Decimal] = None
    copro_soc_conyugal_e: str

class DatosNotario(BaseModel):
    curp: str = Field(default="TOSR520601HOCMXA00")
    num_notaria: int = 4
    entidad_federativa: str = "06"
    adscripcion: str = "MANZANILLO, COLIMA"

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
    pais: str = Field(default="MEX")
    codigo_postal: str

class DatosOperacion(BaseModel):
    num_instrumento_notarial: int
    fecha_inst_notarial: str
    monto_operacion: Decimal
    subtotal: Decimal
    iva: Decimal

class ComplementoNotariosModel(BaseModel):
    datos_operacion: DatosOperacion
    datos_notario: Optional[DatosNotario] = None
    desc_inmuebles: List[DescInmueble]
    datos_adquirientes: List[DatosAdquiriente]
    datos_enajenantes: List[DatosEnajenante]

class InvoiceRequest(BaseModel):
    receptor: Receptor
    conceptos: List[Concepto]
    subtotal: Decimal
    total: Decimal
    copropietarios: Optional[List[Copropietario]] = None
    complemento_notarios: Optional[ComplementoNotariosModel] = None
    datos_extra: Optional[dict] = None

class ISAIRequest(BaseModel):
    operation_price: Decimal
    cadastral_value: Decimal
    rate: Optional[Decimal] = Decimal("0.03")

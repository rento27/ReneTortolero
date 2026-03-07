from pydantic import BaseModel, constr
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
    importe: Decimal
    objeto_imp: str

class Copropietario(BaseModel):
    nombre: str
    rfc: str
    porcentaje: Decimal

class DatosAdquiriente(BaseModel):
    nombre: str
    rfc: str
    apellido_paterno: Optional[str] = None
    apellido_materno: Optional[str] = None
    curp: str
    porcentaje: Optional[Decimal] = None

class DatosEnajenante(BaseModel):
    nombre: str
    rfc: str
    apellido_paterno: Optional[str] = None
    apellido_materno: Optional[str] = None
    curp: str
    porcentaje: Optional[Decimal] = None

class DatosNotario(BaseModel):
    curp: constr(min_length=18, max_length=18)
    num_notaria: int
    entidad_federativa: str
    adscripcion: str

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

class DatosOperacion(BaseModel):
    num_instrumento_notarial: int
    fecha_inst_notarial: str
    monto_operacion: Decimal
    subtotal: Decimal
    iva: Decimal

class ComplementoNotariosModel(BaseModel):
    version: str = "1.0"
    datos_notario: Optional[DatosNotario] = None
    datos_operacion: DatosOperacion
    desc_inmuebles: List[DescInmueble]
    datos_adquiriente: List[DatosAdquiriente]
    datos_enajenante: List[DatosEnajenante]

class InvoiceRequest(BaseModel):
    receptor: Receptor
    conceptos: List[Concepto]
    subtotal: Decimal
    total: Decimal
    copropietarios: Optional[List[Copropietario]] = None
    datos_extra: Optional[dict] = None
    complemento_notarios: Optional[ComplementoNotariosModel] = None

class ISAIRequest(BaseModel):
    operation_price: Decimal
    cadastral_value: Decimal

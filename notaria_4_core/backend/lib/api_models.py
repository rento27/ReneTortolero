from pydantic import BaseModel, Field
from typing import List, Optional, Any
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
    copro_soc_conyugal_e: str
    nombre: str
    rfc: str
    curp: str = Field(default="TOSR520601HOCMXA00")
    porcentaje: Optional[Decimal] = None
    apellido_paterno: Optional[str] = None
    apellido_materno: Optional[str] = None

class DatosEnajenante(BaseModel):
    copro_soc_conyugal_e: str
    nombre: str
    rfc: str
    curp: str = Field(default="TOSR520601HOCMXA00")
    porcentaje: Optional[Decimal] = None
    apellido_paterno: Optional[str] = None
    apellido_materno: Optional[str] = None

class DescInmueble(BaseModel):
    tipo_inmueble: str
    calle: str
    estado: str
    municipio: str
    pais: str = "MEX"
    codigo_postal: str

class DatosNotario(BaseModel):
    curp: str = Field(default="TOSR520601HOCMXA00")
    num_notaria: int = 4
    entidad_federativa: str = "06"
    adscripcion: str = "MANZANILLO COLIMA"

class ComplementoNotariosModel(BaseModel):
    version: str = "1.0"
    datos_notario: Optional[DatosNotario] = None
    fecha_inst_notarial: str
    desc_inmuebles: List[DescInmueble]
    datos_enajenantes: List[DatosEnajenante]
    datos_adquirientes: List[DatosAdquiriente]

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

class InvoiceResponse(BaseModel):
    status: str
    xml_base64: str
    pdf_base64: str

from pydantic import BaseModel, Field, field_validator
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

class DatosUnAdquiriente(BaseModel):
    nombre: str
    apellido_paterno: Optional[str] = None
    apellido_materno: Optional[str] = None
    rfc: str
    curp: str

class DatosAdquirienteCopSC(BaseModel):
    nombre: str
    apellido_paterno: Optional[str] = None
    apellido_materno: Optional[str] = None
    rfc: str
    curp: str
    porcentaje: Decimal

class DatosAdquiriente(BaseModel):
    copro_soc_conyugal_e: str
    datos_un_adquiriente: Optional[DatosUnAdquiriente] = None
    datos_adquirientes_cop_sc: Optional[List[DatosAdquirienteCopSC]] = None

class DatosUnEnajenante(BaseModel):
    nombre: str
    apellido_paterno: Optional[str] = None
    apellido_materno: Optional[str] = None
    rfc: str
    curp: str

class DatosEnajenanteCopSC(BaseModel):
    nombre: str
    apellido_paterno: Optional[str] = None
    apellido_materno: Optional[str] = None
    rfc: str
    curp: str
    porcentaje: Decimal

class DatosEnajenante(BaseModel):
    copro_soc_conyugal_e: str
    datos_un_enajenante: Optional[DatosUnEnajenante] = None
    datos_enajenantes_cop_sc: Optional[List[DatosEnajenanteCopSC]] = None

class DescInmueble(BaseModel):
    tipo_inmueble: str
    calle: str
    municipio: str
    estado: str
    pais: str
    codigo_postal: str
    no_exterior: Optional[str] = None
    no_interior: Optional[str] = None
    colonia: Optional[str] = None
    localidad: Optional[str] = None
    referencia: Optional[str] = None

class DatosOperacion(BaseModel):
    num_instrumento_notarial: int
    fecha_inst_notarial: date
    monto_operacion: Decimal
    subtotal: Decimal
    iva: Decimal

class DatosNotario(BaseModel):
    curp: str = Field(default="TOSR520601HOCMXA00")
    num_notaria: int = 4
    entidad_federativa: str = "06"
    adscripcion: Optional[str] = "MANZANILLO COLIMA"

class ComplementoNotariosModel(BaseModel):
    desc_inmuebles: List[DescInmueble]
    datos_operacion: DatosOperacion
    datos_notario: Optional[DatosNotario] = None
    datos_enajenante: DatosEnajenante
    datos_adquiriente: DatosAdquiriente

class InvoiceRequest(BaseModel):
    receptor: Receptor
    conceptos: List[Concepto]
    subtotal: Decimal
    total: Decimal
    copropietarios: Optional[List[Copropietario]] = None
    datos_extra: Optional[dict] = None
    complemento_notarios: Optional[ComplementoNotariosModel] = None

from pydantic import BaseModel, Field, field_validator
from typing import List, Optional
from decimal import Decimal
from datetime import date

class Receptor(BaseModel):
    rfc: str = Field(..., min_length=12, max_length=13, description="RFC del receptor")
    nombre: str = Field(..., description="Nombre o Razón Social sin régimen societario")
    uso_cfdi: str = Field(..., description="Clave UsoCFDI (ej. G03)")
    domicilio_fiscal: str = Field(..., min_length=5, max_length=5, description="Código Postal")
    regimen_fiscal: str = Field(..., description="Clave Régimen Fiscal (ej. 601)")

class Concepto(BaseModel):
    clave_prod_serv: str
    cantidad: Decimal
    clave_unidad: str
    descripcion: str
    valor_unitario: Decimal
    importe: Decimal
    objeto_imp: str

class DatosNotario(BaseModel):
    num_notaria: int = 4
    entidad_federativa: str = "06" # Colima
    adscripcion: str = "MANZANILLO COLIMA"
    curp: str = Field(..., min_length=18, max_length=18, description="CURP del Notario")

class DatosOperacion(BaseModel):
    num_instrumento_notarial: int
    fecha_inst_notarial: date
    monto_operacion: Decimal
    subtotal: Decimal
    iva: Decimal

class DescInmuebles(BaseModel):
    tipo_inmueble: str # Catalog (e.g. 03)
    calle: str
    no_exterior: Optional[str] = None
    no_interior: Optional[str] = None
    colonia: Optional[str] = None
    localidad: Optional[str] = None
    referencia: Optional[str] = None
    municipio: str
    estado: str
    pais: str = "MEX"
    codigo_postal: str

class DatosAdquiriente(BaseModel):
    nombre: str
    apellido_paterno: Optional[str] = None
    apellido_materno: Optional[str] = None
    rfc: str
    curp: Optional[str] = None
    porcentaje: Optional[Decimal] = None
    copro_soc_conyugal_e: str = "No" # 'Si' o 'No'

class DatosEnajenante(BaseModel):
    nombre: str
    apellido_paterno: Optional[str] = None
    apellido_materno: Optional[str] = None
    rfc: str
    curp: Optional[str] = None
    porcentaje: Optional[Decimal] = None
    copro_soc_conyugal_e: str = "No"

class ComplementoNotarios(BaseModel):
    datos_notario: DatosNotario
    datos_operacion: DatosOperacion
    desc_inmuebles: DescInmuebles
    datos_adquirientes: List[DatosAdquiriente]
    datos_enajenantes: List[DatosEnajenante]

class InvoiceRequest(BaseModel):
    receptor: Receptor
    conceptos: List[Concepto]
    subtotal: Decimal
    total: Decimal
    complemento_notarios: Optional[ComplementoNotarios] = None
    datos_extra: Optional[dict] = None

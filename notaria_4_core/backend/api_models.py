from typing import List, Optional, Union
from decimal import Decimal
from datetime import date
from pydantic import BaseModel, Field, validator

# --- Base Models for Main CFDI ---

class Receptor(BaseModel):
    rfc: str = Field(..., min_length=12, max_length=13)
    nombre: str
    uso_cfdi: str
    domicilio_fiscal: str
    regimen_fiscal: str = Field(..., description="Clave del régimen fiscal (ej. 601, 612)")

class Concepto(BaseModel):
    clave_prod_serv: str
    cantidad: Decimal
    clave_unidad: str
    descripcion: str
    valor_unitario: Decimal
    importe: Decimal
    objeto_imp: str

# --- Models for Complemento Notarios Públicos ---

class DatosNotario(BaseModel):
    curp: str = Field(..., min_length=18, max_length=18)
    num_notaria: int
    entidad_federativa: str # Clave (ej. '06' Colima)
    adscripcion: Optional[str] = None

class DatosOperacion(BaseModel):
    num_instrumento_notarial: int
    fecha_inst_notarial: date
    monto_operacion: Decimal
    subtotal: Decimal
    iva: Decimal

class DescInmueble(BaseModel):
    tipo_inmueble: str # Clave SAT (ej. '03')
    calle: str
    municipio: str
    estado: str # Clave (ej. '06')
    pais: str = "MEX"
    codigo_postal: str
    no_exterior: Optional[str] = None
    no_interior: Optional[str] = None
    colonia: Optional[str] = None
    localidad: Optional[str] = None
    referencia: Optional[str] = None

class Persona(BaseModel):
    nombre: str
    rfc: str
    curp: Optional[str] = None
    apellido_paterno: Optional[str] = None
    apellido_materno: Optional[str] = None

class CopropietarioDetail(Persona):
    porcentaje: Decimal

class DatosEnajenante(BaseModel):
    copro_soc_conyugal_e: str = Field("No", pattern="^(Si|No)$")
    datos_un_enajenante: Optional[Persona] = None
    datos_enajenantes_cop_sc: Optional[List[CopropietarioDetail]] = None

class DatosAdquiriente(BaseModel):
    copro_soc_conyugal_e: str = Field("No", pattern="^(Si|No)$")
    datos_un_adquiriente: Optional[Persona] = None
    datos_adquirientes_cop_sc: Optional[List[CopropietarioDetail]] = None

class ComplementoNotarios(BaseModel):
    desc_inmuebles: List[DescInmueble]
    datos_operacion: DatosOperacion
    datos_notario: DatosNotario
    datos_enajenante: DatosEnajenante
    datos_adquiriente: DatosAdquiriente

# --- Main Request Model ---

class InvoiceRequest(BaseModel):
    receptor: Receptor
    conceptos: List[Concepto]
    subtotal: Decimal
    total: Decimal
    complemento_notarios: Optional[ComplementoNotarios] = None
    datos_extra: Optional[dict] = None

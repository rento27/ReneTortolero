from pydantic import BaseModel, Field
from typing import List, Optional
from decimal import Decimal
from datetime import date

class Receptor(BaseModel):
    rfc: str
    nombre: str
    uso_cfdi: str
    domicilio_fiscal: str
    regimen_fiscal: Optional[str] = "601"  # Default General de Ley PM or specific logic needed

class Concepto(BaseModel):
    clave_prod_serv: str
    cantidad: Decimal
    clave_unidad: str
    descripcion: str
    valor_unitario: Decimal
    importe: Decimal
    objeto_imp: str

class Copropietario(BaseModel):
    """
    Legacy/Internal representation of coproperty for PDF generation or internal logic.
    For XML Complement, use ComplementoNotariosModel.datos_adquirientes.
    """
    nombre: str
    rfc: str
    porcentaje: Decimal

# --- Complemento Notarios Models ---

class DatosNotario(BaseModel):
    curp: str = Field(..., min_length=18, max_length=18)
    num_notaria: int = 4
    entidad_federativa: str = "06"
    adscripcion: str = "MANZANILLO COLIMA" # Matches prompt constant

class DatosOperacion(BaseModel):
    num_instrumento_notarial: int
    fecha_inst_notarial: date
    monto_operacion: Decimal
    subtotal: Decimal
    iva: Decimal

class DescInmueble(BaseModel):
    tipo_inmueble: str  # Catalog value (e.g., 01, 02)
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

class DatosAdquiriente(BaseModel):
    nombre: str
    apellido_paterno: Optional[str] = None
    apellido_materno: Optional[str] = None
    rfc: Optional[str] = None
    curp: Optional[str] = None
    porcentaje: Decimal = Field(..., description="Percentage of ownership (0-100)")
    copro_soc_conyugal_e: str = "No"  # "Si" or "No"

class DatosEnajenante(BaseModel):
    nombre: str
    apellido_paterno: Optional[str] = None
    apellido_materno: Optional[str] = None
    rfc: Optional[str] = None
    curp: Optional[str] = None
    porcentaje: Decimal = Field(..., description="Percentage of ownership (0-100)")
    copro_soc_conyugal_e: str = "No"

class ComplementoNotariosModel(BaseModel):
    datos_notario: DatosNotario
    datos_operacion: DatosOperacion
    desc_inmuebles: List[DescInmueble]
    datos_adquirientes: List[DatosAdquiriente]
    datos_enajenantes: Optional[List[DatosEnajenante]] = None

class InvoiceRequest(BaseModel):
    receptor: Receptor
    conceptos: List[Concepto]
    subtotal: Decimal
    total: Decimal
    copropietarios: Optional[List[Copropietario]] = None
    datos_extra: Optional[dict] = None
    complemento_notarios: Optional[ComplementoNotariosModel] = None

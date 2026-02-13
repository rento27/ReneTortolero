from typing import List, Optional, Union
from decimal import Decimal
from datetime import date
from pydantic import BaseModel, Field

# --- Base CFDI Models ---

class Receptor(BaseModel):
    rfc: str
    nombre: str
    uso_cfdi: str
    domicilio_fiscal: str
    regimen_fiscal: Optional[str] = None # Added based on memory/requirements

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

# --- Complemento Notarios Models ---

class DatosNotarioModel(BaseModel):
    curp: str = Field(..., description="CURP del notario", min_length=18, max_length=18)
    num_notaria: int = Field(default=4, description="Número de la notaría")
    entidad_federativa: str = Field(default="06", description="Entidad Federativa (06=Colima)")
    adscripcion: str = Field(default="MANZANILLO COLIMA", description="Adscripción")

class DatosOperacionModel(BaseModel):
    num_instrumento_notarial: int
    fecha_inst_notarial: date
    monto_operacion: Decimal
    subtotal: Decimal
    iva: Decimal

class DescInmuebleModel(BaseModel):
    tipo_inmueble: str # c_TipoInmueble (e.g. "01" for Terreno, "03" for Casa Habitación)
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

class DatosUnEnajenanteModel(BaseModel):
    nombre: str
    apellido_paterno: str
    apellido_materno: Optional[str] = None
    rfc: str
    curp: str # Requerido para personas físicas

class DatosEnajenantesCopSCModel(BaseModel):
    nombre: str
    apellido_paterno: str
    apellido_materno: Optional[str] = None
    rfc: str
    curp: str
    porcentaje: Decimal

class DatosEnajenanteModel(BaseModel):
    copro_soc_conyugal_e: str = Field(..., pattern="^(Si|No)$")
    datos_un_enajenante: Optional[DatosUnEnajenanteModel] = None
    datos_enajenantes_cop_sc: Optional[List[DatosEnajenantesCopSCModel]] = None

class DatosUnAdquirienteModel(BaseModel):
    nombre: str
    apellido_paterno: Optional[str] = None # Optional per memory
    apellido_materno: Optional[str] = None
    rfc: str
    curp: Optional[str] = None

class DatosAdquirientesCopSCModel(BaseModel):
    nombre: str
    apellido_paterno: Optional[str] = None
    apellido_materno: Optional[str] = None
    rfc: str
    curp: Optional[str] = None
    porcentaje: Decimal

class DatosAdquirienteModel(BaseModel):
    copro_soc_conyugal_e: str = Field(..., pattern="^(Si|No)$")
    datos_un_adquiriente: Optional[DatosUnAdquirienteModel] = None
    datos_adquirientes_cop_sc: Optional[List[DatosAdquirientesCopSCModel]] = None

class ComplementoNotariosModel(BaseModel):
    datos_notario: Optional[DatosNotarioModel] = None # Optional, can use defaults in logic
    datos_operacion: DatosOperacionModel
    desc_inmuebles: List[DescInmuebleModel]
    datos_enajenante: DatosEnajenanteModel
    datos_adquiriente: DatosAdquirienteModel

# --- Main Invoice Request ---

class InvoiceRequest(BaseModel):
    receptor: Receptor
    conceptos: List[Concepto]
    subtotal: Decimal
    total: Decimal
    # Deprecated/Simple copropietarios field vs Full Complement Model
    copropietarios: Optional[List[Copropietario]] = None
    complemento_notarios: Optional[ComplementoNotariosModel] = None
    datos_extra: Optional[dict] = None

class ISAIRequest(BaseModel):
    operation_price: Decimal
    cadastral_value: Decimal

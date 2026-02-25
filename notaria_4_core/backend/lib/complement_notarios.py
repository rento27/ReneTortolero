from datetime import date
from decimal import Decimal
from typing import List, Union
import logging
from .api_models import ComplementoNotariosModel, DatosAdquiriente, DatosEnajenante

logger = logging.getLogger(__name__)

# Try importing satcfdi classes (Mock safe)
try:
    from satcfdi.create.cfd.notariospublicos10 import NotariosPublicos
except ImportError:
    NotariosPublicos = None

def split_name(full_name: str):
    """
    Heuristic to split full name into (Paterno, Materno) if not provided.
    Assumes standard Mexican name structure: [Nombres] [Paterno] [Materno]
    This is a fallback and not perfect.
    """
    parts = full_name.strip().split()
    if len(parts) >= 3:
        return parts[-2], parts[-1]
    elif len(parts) == 2:
        return parts[-1], "" # No materno?
    return "", ""

def validate_percentages(percentages: List[Decimal]):
    """
    Validates that the sum of percentages is exactly 100.00.
    """
    total = sum(p for p in percentages if p is not None)
    if total != Decimal("100.00"):
        raise ValueError(f"Sum of percentages must be 100.00%, got {total}")

def create_complemento_notarios(data: ComplementoNotariosModel):
    if not NotariosPublicos:
        logger.error("satcfdi.create.cfd.notariospublicos10 not found")
        return None

    # 1. Validate Date
    if data.datos_operacion.fecha_inst_notarial > date.today():
        raise ValueError(f"FechaInstNotarial {data.datos_operacion.fecha_inst_notarial} cannot be in the future.")

    # 2. Build DatosAdquirientes
    adquirientes_data = {}
    is_copro_adq = any(a.copro_soc_conyugal_e == 'Si' for a in data.datos_adquirientes)

    if is_copro_adq:
        validate_percentages([a.porcentaje for a in data.datos_adquirientes])
        adquirientes_list = []
        for a in data.datos_adquirientes:
            paterno, materno = (a.apellido_paterno, a.apellido_materno)
            if not paterno:
                p_split, m_split = split_name(a.nombre)
                paterno = paterno or p_split
                materno = materno or m_split

            adquirientes_list.append({
                'Nombre': a.nombre,
                'ApellidoPaterno': paterno,
                'ApellidoMaterno': materno,
                'RFC': a.rfc,
                'CURP': a.curp,
                'Porcentaje': a.porcentaje
            })
        adquirientes_data = {
            'CoproSocConyugalE': 'Si',
            'DatosAdquirientesCopSC': adquirientes_list
        }
    else:
        if len(data.datos_adquirientes) != 1:
            raise ValueError("For CoproSocConyugalE='No' (Adquiriente), exactly one record is required.")
        a = data.datos_adquirientes[0]
        paterno, materno = (a.apellido_paterno, a.apellido_materno)
        if not paterno:
            p_split, m_split = split_name(a.nombre)
            paterno = paterno or p_split
            materno = materno or m_split

        adquirientes_data = {
            'CoproSocConyugalE': 'No',
            'DatosUnAdquiriente': {
                'Nombre': a.nombre,
                'ApellidoPaterno': paterno,
                'ApellidoMaterno': materno,
                'RFC': a.rfc,
                'CURP': a.curp
            }
        }

    # 3. Build DatosEnajenantes
    enajenantes_data = {}
    is_copro_enaj = any(e.copro_soc_conyugal_e == 'Si' for e in data.datos_enajenantes)

    if is_copro_enaj:
        validate_percentages([e.porcentaje for e in data.datos_enajenantes])
        enajenantes_list = []
        for e in data.datos_enajenantes:
            paterno, materno = (e.apellido_paterno, e.apellido_materno)
            if not paterno:
                p_split, m_split = split_name(e.nombre)
                paterno = paterno or p_split
                materno = materno or m_split

            enajenantes_list.append({
                'Nombre': e.nombre,
                'ApellidoPaterno': paterno,
                'ApellidoMaterno': materno,
                'RFC': e.rfc,
                'CURP': e.curp,
                'Porcentaje': e.porcentaje
            })
        enajenantes_data = {
            'CoproSocConyugalE': 'Si',
            'DatosEnajenantesCopSC': enajenantes_list
        }
    else:
        if len(data.datos_enajenantes) != 1:
            raise ValueError("For CoproSocConyugalE='No' (Enajenante), exactly one record is required.")
        e = data.datos_enajenantes[0]
        paterno, materno = (e.apellido_paterno, e.apellido_materno)
        if not paterno:
            p_split, m_split = split_name(e.nombre)
            paterno = paterno or p_split
            materno = materno or m_split

        enajenantes_data = {
            'CoproSocConyugalE': 'No',
            'DatosUnEnajenante': {
                'Nombre': e.nombre,
                'ApellidoPaterno': paterno,
                'ApellidoMaterno': materno,
                'RFC': e.rfc,
                'CURP': e.curp
            }
        }

    # 4. DescInmuebles
    inmuebles_list = []
    for i in data.desc_inmuebles:
        inmuebles_list.append({
            'TipoInmueble': i.tipo_inmueble,
            'Calle': i.calle,
            'NoExterior': i.no_exterior,
            'NoInterior': i.no_interior,
            'Colonia': i.colonia,
            'Localidad': i.localidad,
            'Referencia': i.referencia,
            'Municipio': i.municipio,
            'Estado': i.estado,
            'Pais': i.pais,
            'CodigoPostal': i.codigo_postal
        })

    # 5. Construct Complement
    # Using dictionary unpacking for internal nodes if needed, or direct arguments
    # satcfdi NotariosPublicos expects snake_case arguments that match the XSD structure

    # Get CURP from input or default
    notary_curp = "TOSR520601HOCMXA00" # Fallback/Default
    if data.datos_notario and data.datos_notario.curp:
        notary_curp = data.datos_notario.curp

    return NotariosPublicos(
        version='1.0',
        datos_notario={
            'CURP': notary_curp,
            'NumNotaria': 4,
            'EntidadFederativa': '06',
            'Adscripcion': 'MANZANILLO, COLIMA'
        },
        datos_operacion={
            'NumInstrumentoNotarial': data.datos_operacion.num_instrumento_notarial,
            'FechaInstNotarial': data.datos_operacion.fecha_inst_notarial,
            'MontoOperacion': data.datos_operacion.monto_operacion,
            'SubTotal': data.datos_operacion.subtotal,
            'IVA': data.datos_operacion.iva
        },
        datos_adquirientes=adquirientes_data,
        datos_enajenantes=enajenantes_data,
        desc_inmuebles=inmuebles_list
    )

from decimal import Decimal
from typing import Tuple, List, Optional
from datetime import datetime
from .api_models import ComplementoNotariosModel, DatosAdquiriente, DatosEnajenante, DescInmueble, DatosOperacion, DatosNotario
import logging

# satcfdi v4 specific imports
try:
    from satcfdi.create.cfd.notariospublicos10 import (
        NotariosPublicos,
        DescInmueble as SatDescInmueble,
        DatosOperacion as SatDatosOperacion,
        DatosNotario as SatDatosNotario,
        DatosEnajenante as SatDatosEnajenante,
        DatosUnEnajenante as SatDatosUnEnajenante,
        DatosEnajenantesCopSC as SatDatosEnajenantesCopSC,
        DatosAdquiriente as SatDatosAdquiriente,
        DatosUnAdquiriente as SatDatosUnAdquiriente,
        DatosAdquirientesCopSC as SatDatosAdquirientesCopSC
    )
except ImportError:
    NotariosPublicos = None

logger = logging.getLogger(__name__)

def split_name(full_name: str) -> Tuple[str, str, str]:
    """
    Splits a full name into (nombre, apellido_paterno, apellido_materno).
    Returns (full_name, '', '') for a single word to avoid ambiguous surname assignments.
    """
    parts = full_name.strip().split()
    if len(parts) == 1:
        return full_name, '', ''
    elif len(parts) == 2:
        return parts[0], parts[1], ''
    else:
        # Assume last two words are apellidos
        nombre = ' '.join(parts[:-2])
        return nombre, parts[-2], parts[-1]

def create_complemento_notarios(data: ComplementoNotariosModel):
    if not NotariosPublicos:
        logger.error("satcfdi library not found. Cannot create complemento.")
        return None

    # Validate FechaInstNotarial
    try:
        fecha_inst = datetime.fromisoformat(data.datos_operacion.fecha_inst_notarial)
        if fecha_inst > datetime.now():
            raise ValueError("FechaInstNotarial cannot be in the future.")
    except ValueError as e:
        if "future" in str(e):
            raise e
        # If it's not isoformat, fallback or other validation could happen

    # Process Inmuebles
    inmuebles = []
    for inm in data.desc_inmuebles:
        inmuebles.append(SatDescInmueble(
            tipo_inmueble=inm.tipo_inmueble,
            calle=inm.calle,
            municipio=inm.municipio,
            estado=inm.estado, # Ensure 'estado' is used
            pais=inm.pais,
            codigo_postal=inm.codigo_postal,
            no_exterior=inm.no_exterior,
            no_interior=inm.no_interior,
            colonia=inm.colonia,
            localidad=inm.localidad,
            referencia=inm.referencia
        ))

    # Process Operacion
    operacion = SatDatosOperacion(
        num_instrumento_notarial=data.datos_operacion.num_instrumento_notarial,
        fecha_inst_notarial=data.datos_operacion.fecha_inst_notarial,
        monto_operacion=data.datos_operacion.monto_operacion,
        subtotal=data.datos_operacion.subtotal,
        iva=data.datos_operacion.iva
    )

    # Process Notario
    notario = SatDatosNotario(
        curp=data.datos_notario.curp,
        num_notaria=4,
        entidad_federativa='06',
        adscripcion='MANZANILLO COLIMA'
    )

    # Process Enajenantes
    enajenante_wrapper = _build_enajenante(data.datos_enajenante)

    # Process Adquirientes
    adquiriente_wrapper = _build_adquiriente(data.datos_adquiriente)

    comp = NotariosPublicos(
        desc_inmuebles=inmuebles,
        datos_operacion=operacion,
        datos_notario=notario,
        datos_enajenante=enajenante_wrapper,
        datos_adquiriente=adquiriente_wrapper
    )
    return comp

def _build_enajenante(enajenantes: List[DatosEnajenante]):
    if not enajenantes:
        raise ValueError("At least one enajenante is required.")

    # Check if copro is 'No'. If so, list must have exactly 1.
    copro_no = any(e.copro_soc_conyugal_e == 'No' for e in enajenantes)
    if copro_no and len(enajenantes) != 1:
        raise ValueError("If CoproSocConyugalE is 'No', exactly one Enajenante must be provided.")

    # Check sum of percentages if provided
    porcentajes = [e.porcentaje for e in enajenantes if e.porcentaje is not None]
    if porcentajes:
        if sum(porcentajes) != Decimal('100.00'):
            raise ValueError(f"Sum of percentages for enajenantes must be exactly 100.00, got {sum(porcentajes)}")

    if enajenantes[0].copro_soc_conyugal_e == 'No':
        e = enajenantes[0]
        nom, ap, am = split_name(e.nombre)
        if e.apellido_paterno is not None:
            ap = e.apellido_paterno
        if e.apellido_materno is not None:
            am = e.apellido_materno

        un_enajenante = SatDatosUnEnajenante(
            nombre=nom,
            apellido_paterno=ap,
            apellido_materno=am,
            rfc=e.rfc,
            curp=e.curp
        )
        return SatDatosEnajenante(
            copro_soc_conyugal_e='No',
            datos_un_enajenante=un_enajenante
        )
    else:
        # Copro is Si
        lista_cop = []
        for e in enajenantes:
            nom, ap, am = split_name(e.nombre)
            if e.apellido_paterno is not None:
                ap = e.apellido_paterno
            if e.apellido_materno is not None:
                am = e.apellido_materno

            lista_cop.append(SatDatosEnajenantesCopSC(
                nombre=nom,
                apellido_paterno=ap,
                apellido_materno=am,
                rfc=e.rfc,
                curp=e.curp,
                porcentaje=e.porcentaje
            ))
        return SatDatosEnajenante(
            copro_soc_conyugal_e='Si',
            datos_enajenantes_cop_sc=lista_cop
        )


def _build_adquiriente(adquirientes: List[DatosAdquiriente]):
    if not adquirientes:
        raise ValueError("At least one adquiriente is required.")

    # Check if copro is 'No'. If so, list must have exactly 1.
    copro_no = any(a.copro_soc_conyugal_e == 'No' for a in adquirientes)
    if copro_no and len(adquirientes) != 1:
        raise ValueError("If CoproSocConyugalE is 'No', exactly one Adquiriente must be provided.")

    # Check sum of percentages if provided
    porcentajes = [a.porcentaje for a in adquirientes if a.porcentaje is not None]
    if porcentajes:
        if sum(porcentajes) != Decimal('100.00'):
            raise ValueError(f"Sum of percentages for adquirientes must be exactly 100.00, got {sum(porcentajes)}")

    if adquirientes[0].copro_soc_conyugal_e == 'No':
        a = adquirientes[0]
        nom, ap, am = split_name(a.nombre)
        if a.apellido_paterno is not None:
            ap = a.apellido_paterno
        if a.apellido_materno is not None:
            am = a.apellido_materno

        un_adquiriente = SatDatosUnAdquiriente(
            nombre=nom,
            apellido_paterno=ap,
            apellido_materno=am,
            rfc=a.rfc,
            curp=a.curp
        )
        return SatDatosAdquiriente(
            copro_soc_conyugal_e='No',
            datos_un_adquiriente=un_adquiriente
        )
    else:
        # Copro is Si
        lista_cop = []
        for a in adquirientes:
            nom, ap, am = split_name(a.nombre)
            if a.apellido_paterno is not None:
                ap = a.apellido_paterno
            if a.apellido_materno is not None:
                am = a.apellido_materno

            lista_cop.append(SatDatosAdquirientesCopSC(
                nombre=nom,
                apellido_paterno=ap,
                apellido_materno=am,
                rfc=a.rfc,
                curp=a.curp,
                porcentaje=a.porcentaje
            ))
        return SatDatosAdquiriente(
            copro_soc_conyugal_e='Si',
            datos_adquirientes_cop_sc=lista_cop
        )

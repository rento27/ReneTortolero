from datetime import datetime
from decimal import Decimal
import logging
from typing import Tuple

logger = logging.getLogger(__name__)

try:
    from satcfdi.create.cfd import notariospublicos10
except ImportError:
    notariospublicos10 = None

from .fiscal_engine import validate_copropiedad, sanitize_name
from .api_models import ComplementoNotariosModel


def split_name(full_name: str) -> Tuple[str, str, str]:
    """
    Heuristic to split a full name into (nombre, apellido_paterno, apellido_materno).
    Returns (full_name, '', '') if it cannot be safely split (e.g., single word).
    """
    parts = full_name.strip().split()
    if len(parts) == 1:
        return (full_name, '', '')
    elif len(parts) == 2:
        return (parts[0], parts[1], '')
    elif len(parts) == 3:
        return (parts[0], parts[1], parts[2])
    else:
        # Assuming first two parts are the name, and last two are surnames.
        # This is a basic fallback and might need manual adjustment.
        return (' '.join(parts[:-2]), parts[-2], parts[-1])


def _build_datos_adquiriente(adquirientes: list) -> dict:
    if not adquirientes:
        return {}

    # If single non-copro
    if len(adquirientes) == 1 and adquirientes[0].copro_soc_conyugal_e == "No":
        adq = adquirientes[0]
        nombre, ap_pat, ap_mat = adq.nombre, adq.apellido_paterno, adq.apellido_materno
        if not ap_pat and not ap_mat:
            nombre, ap_pat, ap_mat = split_name(adq.nombre)

        datos_un_adquiriente = notariospublicos10.DatosUnAdquiriente(
            nombre=sanitize_name(nombre),
            apellido_paterno=sanitize_name(ap_pat) if ap_pat else None,
            apellido_materno=sanitize_name(ap_mat) if ap_mat else None,
            rfc=adq.rfc,
            curp=adq.curp
        )
        return {"datos_un_adquiriente": datos_un_adquiriente}
    else:
        # Copro
        copro_list = []
        percentages = []
        for adq in adquirientes:
            nombre, ap_pat, ap_mat = adq.nombre, adq.apellido_paterno, adq.apellido_materno
            if not ap_pat and not ap_mat:
                nombre, ap_pat, ap_mat = split_name(adq.nombre)

            copro = notariospublicos10.DatosAdquirienteCopSC(
                nombre=sanitize_name(nombre),
                apellido_paterno=sanitize_name(ap_pat) if ap_pat else None,
                apellido_materno=sanitize_name(ap_mat) if ap_mat else None,
                rfc=adq.rfc,
                curp=adq.curp,
                porcentaje=adq.porcentaje
            )
            copro_list.append(copro)
            if adq.porcentaje is not None:
                percentages.append(adq.porcentaje)

        if percentages:
            validate_copropiedad(percentages)

        return {"datos_adquirientes_cop_sc": copro_list}


def _build_datos_enajenante(enajenantes: list) -> dict:
    if not enajenantes:
        return {}

    # If single non-copro
    if len(enajenantes) == 1 and enajenantes[0].copro_soc_conyugal_e == "No":
        enaj = enajenantes[0]
        nombre, ap_pat, ap_mat = enaj.nombre, enaj.apellido_paterno, enaj.apellido_materno
        if not ap_pat and not ap_mat:
            nombre, ap_pat, ap_mat = split_name(enaj.nombre)

        datos_un_enajenante = notariospublicos10.DatosUnEnajenante(
            nombre=sanitize_name(nombre),
            apellido_paterno=sanitize_name(ap_pat) if ap_pat else None,
            apellido_materno=sanitize_name(ap_mat) if ap_mat else None,
            rfc=enaj.rfc,
            curp=enaj.curp
        )
        return {"datos_un_enajenante": datos_un_enajenante}
    else:
        # Copro
        copro_list = []
        percentages = []
        for enaj in enajenantes:
            nombre, ap_pat, ap_mat = enaj.nombre, enaj.apellido_paterno, enaj.apellido_materno
            if not ap_pat and not ap_mat:
                nombre, ap_pat, ap_mat = split_name(enaj.nombre)

            copro = notariospublicos10.DatosEnajenanteCopSC(
                nombre=sanitize_name(nombre),
                apellido_paterno=sanitize_name(ap_pat) if ap_pat else None,
                apellido_materno=sanitize_name(ap_mat) if ap_mat else None,
                rfc=enaj.rfc,
                curp=enaj.curp,
                porcentaje=enaj.porcentaje
            )
            copro_list.append(copro)
            if enaj.porcentaje is not None:
                percentages.append(enaj.porcentaje)

        if percentages:
            validate_copropiedad(percentages)

        return {"datos_enajenantes_cop_sc": copro_list}


def create_complemento_notarios(data: ComplementoNotariosModel) -> notariospublicos10.NotariosPublicos:
    """
    Creates a CFDI NotariosPublicos 1.0 complement.
    """
    if not notariospublicos10:
        logger.error("satcfdi notariospublicos10 module not available.")
        return None

    # Validate Dates
    fecha_inst = datetime.fromisoformat(data.datos_operacion.fecha_inst_notarial)
    if fecha_inst > datetime.now():
         raise ValueError(f"FechaInstNotarial cannot be in the future: {fecha_inst}")

    # Build DescInmuebles
    desc_inmuebles = []
    for inm in data.desc_inmuebles:
        desc = notariospublicos10.DescInmueble(
            tipo_inmueble=inm.tipo_inmueble,
            calle=inm.calle,
            no_exterior=inm.no_exterior,
            no_interior=inm.no_interior,
            colonia=inm.colonia,
            localidad=inm.localidad,
            referencia=inm.referencia,
            municipio=inm.municipio,
            estado=inm.estado,
            pais=inm.pais,
            codigo_postal=inm.codigo_postal
        )
        desc_inmuebles.append(desc)

    # Build DatosOperacion
    datos_operacion = notariospublicos10.DatosOperacion(
        num_instrumento_notarial=data.datos_operacion.num_instrumento_notarial,
        fecha_inst_notarial=fecha_inst,
        monto_operacion=data.datos_operacion.monto_operacion,
        subtotal=data.datos_operacion.subtotal,
        iva=data.datos_operacion.iva
    )

    # Build DatosNotario
    # Default is the one passed, but fallback to values as requested in instructions
    curp = data.datos_notario.curp if data.datos_notario else "TOSR520601HOCMXA00"
    num_notaria = data.datos_notario.num_notaria if data.datos_notario else 4
    entidad_federativa = data.datos_notario.entidad_federativa if data.datos_notario else "06"
    adscripcion = data.datos_notario.adscripcion if data.datos_notario else "MANZANILLO, COLIMA"

    datos_notario = notariospublicos10.DatosNotario(
        curp=curp,
        num_notaria=num_notaria,
        entidad_federativa=entidad_federativa,
        adscripcion=adscripcion
    )

    # Build Enajenante and Adquiriente wrappers
    datos_adquiriente_kwargs = _build_datos_adquiriente(data.datos_adquiriente)
    datos_enajenante_kwargs = _build_datos_enajenante(data.datos_enajenante)

    datos_adquiriente_wrapper = notariospublicos10.DatosAdquiriente(
        copro_soc_conyugal_e=data.datos_adquiriente[0].copro_soc_conyugal_e if data.datos_adquiriente else "No",
        **datos_adquiriente_kwargs
    )

    datos_enajenante_wrapper = notariospublicos10.DatosEnajenante(
        copro_soc_conyugal_e=data.datos_enajenante[0].copro_soc_conyugal_e if data.datos_enajenante else "No",
        **datos_enajenante_kwargs
    )

    # Construct the final NotariosPublicos complement
    return notariospublicos10.NotariosPublicos(
        desc_inmuebles=desc_inmuebles,
        datos_operacion=datos_operacion,
        datos_notario=datos_notario,
        datos_enajenante=datos_enajenante_wrapper,
        datos_adquiriente=datos_adquiriente_wrapper
    )

from decimal import Decimal
from typing import List, Tuple, Dict, Any
from .api_models import DatosAdquiriente, DatosEnajenante, DatosNotario, ComplementoNotariosModel
from .fiscal_engine import sanitize_name, validate_copropiedad
from datetime import datetime

# Check for satcfdi availability
try:
    from satcfdi.create.cfd.notariospublicos10 import (
        NotariosPublicos, DescInmueble, DatosOperacion,
        DatosAdquiriente as CompDatosAdquiriente, DatosUnAdquiriente, DatosAdquirienteCopSC,
        DatosEnajenante as CompDatosEnajenante, DatosUnEnajenante, DatosEnajenanteCopSC
    )
except ImportError:
    NotariosPublicos = None
    DescInmueble = None
    DatosOperacion = None
    CompDatosAdquiriente = None
    DatosUnAdquiriente = None
    DatosAdquirienteCopSC = None
    CompDatosEnajenante = None
    DatosUnEnajenante = None
    DatosEnajenanteCopSC = None

def split_name(full_name: str) -> Tuple[str, str, str]:
    """
    Heuristically splits a full name into (nombre, apellido_paterno, apellido_materno).
    Returns (full_name, '', '') if it's a single word to avoid ambiguous assignment.
    """
    parts = full_name.split()
    if len(parts) <= 1:
        return (full_name, "", "")

    # Simple heuristic: last two words are last names, the rest is the first name.
    if len(parts) == 2:
        return (parts[0], parts[1], "")

    return (" ".join(parts[:-2]), parts[-2], parts[-1])

def create_complemento_notarios(model: ComplementoNotariosModel) -> Any:
    """
    Creates the NotariosPublicos complement.
    Validates rules based on notaria requirements.
    """
    if not NotariosPublicos:
        raise RuntimeError("satcfdi library is not available.")

    # Validate Date
    fecha_inst = datetime.fromisoformat(model.datos_operacion['fecha_inst_notarial'])
    if fecha_inst > datetime.now():
        raise ValueError("FechaInstNotarial cannot be in the future.")

    # Desc Inmuebles
    desc_inmuebles = []
    for inm in model.desc_inmuebles:
        desc_inmuebles.append(DescInmueble(
            tipo_inmueble=inm['tipo_inmueble'],
            calle=inm['calle'],
            estado=inm.get('estado'),
            pais=inm.get('pais', 'MEX'),
            codigo_postal=inm['codigo_postal']
        ))

    # Adquirientes
    adquirientes_is_copro = any(a.copro_soc_conyugal_e == 'Si' for a in model.datos_adquirientes)

    # Validation: If copro is 'No', there must be exactly one item
    if not adquirientes_is_copro and len(model.datos_adquirientes) != 1:
         raise ValueError("If CoproSocConyugalE is 'No', there must be exactly one Adquiriente.")

    datos_adquiriente = None
    if not adquirientes_is_copro:
        a = model.datos_adquirientes[0]
        n, p, m = split_name(a.nombre)
        nombre = sanitize_name(a.nombre) if not a.apellido_paterno else a.nombre
        apaterno = a.apellido_paterno if a.apellido_paterno is not None else p
        amaterno = a.apellido_materno if a.apellido_materno is not None else m

        datos_un_adquiriente = DatosUnAdquiriente(
            nombre=nombre,
            apellido_paterno=apaterno,
            apellido_materno=amaterno,
            rfc=a.rfc
        )
        datos_adquiriente = CompDatosAdquiriente(
            copro_soc_conyugal_e="No",
            datos_un_adquiriente=datos_un_adquiriente
        )
    else:
        # Validate sum to 100%
        percs = [Decimal(str(a.porcentaje)) for a in model.datos_adquirientes if a.porcentaje is not None]
        if percs:
            validate_copropiedad(percs)

        cop_list = []
        for a in model.datos_adquirientes:
            n, p, m = split_name(a.nombre)
            nombre = sanitize_name(a.nombre) if not a.apellido_paterno else a.nombre
            apaterno = a.apellido_paterno if a.apellido_paterno is not None else p
            amaterno = a.apellido_materno if a.apellido_materno is not None else m

            cop_list.append(DatosAdquirienteCopSC(
                nombre=nombre,
                apellido_paterno=apaterno,
                apellido_materno=amaterno,
                rfc=a.rfc,
                porcentaje=Decimal(str(a.porcentaje)) if a.porcentaje else None
            ))

        datos_adquiriente = CompDatosAdquiriente(
            copro_soc_conyugal_e="Si",
            datos_adquirientes_cop_sc=cop_list
        )


    # Enajenantes
    enajenantes_is_copro = any(e.copro_soc_conyugal_e == 'Si' for e in model.datos_enajenantes)

    # Validation: If copro is 'No', there must be exactly one item
    if not enajenantes_is_copro and len(model.datos_enajenantes) != 1:
         raise ValueError("If CoproSocConyugalE is 'No', there must be exactly one Enajenante.")

    datos_enajenante = None
    if not enajenantes_is_copro:
        e = model.datos_enajenantes[0]
        n, p, m = split_name(e.nombre)
        nombre = sanitize_name(e.nombre) if not e.apellido_paterno else e.nombre
        apaterno = e.apellido_paterno if e.apellido_paterno is not None else p
        amaterno = e.apellido_materno if e.apellido_materno is not None else m

        datos_un_enajenante = DatosUnEnajenante(
            nombre=nombre,
            apellido_paterno=apaterno,
            apellido_materno=amaterno,
            rfc=e.rfc,
            curp=e.curp
        )
        datos_enajenante = CompDatosEnajenante(
            copro_soc_conyugal_e="No",
            datos_un_enajenante=datos_un_enajenante
        )
    else:
        # Validate sum to 100%
        percs = [Decimal(str(e.porcentaje)) for e in model.datos_enajenantes if e.porcentaje is not None]
        if percs:
            validate_copropiedad(percs)

        cop_list = []
        for e in model.datos_enajenantes:
            n, p, m = split_name(e.nombre)
            nombre = sanitize_name(e.nombre) if not e.apellido_paterno else e.nombre
            apaterno = e.apellido_paterno if e.apellido_paterno is not None else p
            amaterno = e.apellido_materno if e.apellido_materno is not None else m

            cop_list.append(DatosEnajenanteCopSC(
                nombre=nombre,
                apellido_paterno=apaterno,
                apellido_materno=amaterno,
                rfc=e.rfc,
                curp=e.curp,
                porcentaje=Decimal(str(e.porcentaje)) if e.porcentaje else None
            ))

        datos_enajenante = CompDatosEnajenante(
            copro_soc_conyugal_e="Si",
            datos_enajenantes_cop_sc=cop_list
        )

    return NotariosPublicos(
        desc_inmuebles=desc_inmuebles,
        datos_operacion=DatosOperacion(
            num_instrumento_notarial=model.datos_operacion['num_instrumento_notarial'],
            fecha_inst_notarial=model.datos_operacion['fecha_inst_notarial'],
            monto_operacion=Decimal(str(model.datos_operacion['monto_operacion'])),
            subtotal=Decimal(str(model.datos_operacion['subtotal'])),
            iva=Decimal(str(model.datos_operacion['iva']))
        ),
        datos_notario={
            'Curp': model.datos_notario.curp,
            'NumNotaria': model.datos_notario.num_notaria,
            'EntidadFederativa': model.datos_notario.entidad_federativa,
            'Adscripcion': model.datos_notario.adscripcion
        },
        datos_adquiriente=datos_adquiriente,
        datos_enajenante=datos_enajenante
    )

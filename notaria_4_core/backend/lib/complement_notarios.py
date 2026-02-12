from decimal import Decimal
from typing import List, Union
from datetime import date

from satcfdi.create.cfd.notariospublicos10 import (
    NotariosPublicos,
    DatosNotario as SatDatosNotario,
    DatosOperacion as SatDatosOperacion,
    DescInmueble as SatDescInmueble,
    DatosAdquiriente as SatDatosAdquiriente,
    DatosUnAdquiriente as SatDatosUnAdquiriente,
    DatosAdquirienteCopSC as SatDatosAdquirienteCopSC,
    DatosEnajenante as SatDatosEnajenante,
    DatosUnEnajenante as SatDatosUnEnajenante,
    DatosEnajenanteCopSC as SatDatosEnajenanteCopSC
)

from .api_models import ComplementoNotarios, DatosAdquiriente, DatosEnajenante
from .fiscal_engine import validate_copropiedad, sanitize_name

def create_complemento_notarios(data: ComplementoNotarios) -> NotariosPublicos:
    # 1. Datos Notario
    # Validate CURP (basic length check, could be more strict)
    if len(data.datos_notario.curp) != 18:
        raise ValueError(f"CURP length must be 18, got {len(data.datos_notario.curp)}")

    notario = SatDatosNotario(
        curp=data.datos_notario.curp,
        num_notaria=data.datos_notario.num_notaria,
        entidad_federativa=data.datos_notario.entidad_federativa,
        adscripcion=data.datos_notario.adscripcion
    )

    # 2. Datos Operacion
    if data.datos_operacion.fecha_inst_notarial > date.today():
        raise ValueError(f"FechaInstNotarial cannot be in the future: {data.datos_operacion.fecha_inst_notarial}")

    operacion = SatDatosOperacion(
        num_instrumento_notarial=data.datos_operacion.num_instrumento_notarial,
        fecha_inst_notarial=data.datos_operacion.fecha_inst_notarial,
        monto_operacion=data.datos_operacion.monto_operacion,
        subtotal=data.datos_operacion.subtotal,
        iva=data.datos_operacion.iva
    )

    # 3. Desc Inmuebles
    inmuebles = [
        SatDescInmueble(
            tipo_inmueble=i.tipo_inmueble,
            calle=i.calle,
            no_exterior=i.no_exterior,
            no_interior=i.no_interior,
            colonia=i.colonia,
            localidad=i.localidad,
            referencia=i.referencia,
            municipio=i.municipio,
            estado=i.estado,
            pais=i.pais,
            codigo_postal=i.codigo_postal
        ) for i in data.desc_inmuebles
    ]

    # 4. Datos Adquiriente
    adquiriente_container = _process_adquirientes(data.datos_adquirientes)

    # 5. Datos Enajenante
    enajenante_container = _process_enajenantes(data.datos_enajenantes)

    return NotariosPublicos(
        datos_notario=notario,
        datos_operacion=operacion,
        desc_inmuebles=inmuebles,
        datos_adquiriente=adquiriente_container,
        datos_enajenante=enajenante_container
    )

def _split_name_if_needed(nombre_completo: str, paterno: str = None, materno: str = None):
    """
    Splits a full name into (nombre, paterno, materno) if paterno/materno are missing.
    Very basic heuristic: assume "Nombre ApellidoPaterno ApellidoMaterno" structure.
    """
    # Sanitize inputs
    nombre_completo = sanitize_name(nombre_completo)
    paterno = sanitize_name(paterno) if paterno else None
    materno = sanitize_name(materno) if materno else None

    if paterno:
        return nombre_completo, paterno, materno

    parts = nombre_completo.split()
    if len(parts) >= 3:
        # Assume last two are surnames
        n = " ".join(parts[:-2])
        p = parts[-2]
        m = parts[-1]
        return n, p, m
    elif len(parts) == 2:
        # Assume one surname
        n = parts[0]
        p = parts[1]
        return n, p, None
    else:
        # Only one name provided? This is problematic for strict requirements.
        # Fallback to avoid complete crash but likely invalid for SAT.
        return nombre_completo, "X", None

def _process_adquirientes(adquirientes: list[DatosAdquiriente]) -> SatDatosAdquiriente:
    if not adquirientes:
        raise ValueError("Must have at least one Adquiriente")

    copro_flag = "Si" if len(adquirientes) > 1 or adquirientes[0].copro_soc_conyugal_e == "Si" else "No"

    if copro_flag == "No":
        p = adquirientes[0]
        n, pat, mat = _split_name_if_needed(p.nombre, p.apellido_paterno, p.apellido_materno)

        # DatosUnAdquiriente treats paterno as optional but we provide it if available
        un_adquiriente = SatDatosUnAdquiriente(
            nombre=n,
            apellido_paterno=pat,
            apellido_materno=mat,
            rfc=p.rfc,
            curp=p.curp
        )
        return SatDatosAdquiriente(
            copro_soc_conyugal_e="No",
            datos_un_adquiriente=un_adquiriente
        )
    else:
        cop_list = []
        percentages = []
        for p in adquirientes:
            percentages.append(p.porcentaje)
            n, pat, mat = _split_name_if_needed(p.nombre, p.apellido_paterno, p.apellido_materno)

            cop_list.append(SatDatosAdquirienteCopSC(
                nombre=n,
                apellido_paterno=pat,
                apellido_materno=mat,
                rfc=p.rfc,
                curp=p.curp,
                porcentaje=p.porcentaje
            ))

        validate_copropiedad(percentages)

        return SatDatosAdquiriente(
            copro_soc_conyugal_e="Si",
            datos_adquirientes_cop_sc=cop_list
        )

def _process_enajenantes(enajenantes: list[DatosEnajenante]) -> SatDatosEnajenante:
    if not enajenantes:
        raise ValueError("Must have at least one Enajenante")

    copro_flag = "Si" if len(enajenantes) > 1 or enajenantes[0].copro_soc_conyugal_e == "Si" else "No"

    if copro_flag == "No":
        p = enajenantes[0]
        n, pat, mat = _split_name_if_needed(p.nombre, p.apellido_paterno, p.apellido_materno)

        # DatosUnEnajenante strictly requires paterno and curp
        if not pat:
             raise ValueError(f"Apellido Paterno is required for Enajenante: {p.nombre}")
        if not p.curp:
             raise ValueError(f"CURP is required for Enajenante: {p.nombre}")

        un_enajenante = SatDatosUnEnajenante(
            nombre=n,
            apellido_paterno=pat,
            apellido_materno=mat,
            rfc=p.rfc,
            curp=p.curp
        )
        return SatDatosEnajenante(
            copro_soc_conyugal_e="No",
            datos_un_enajenante=un_enajenante
        )
    else:
        cop_list = []
        percentages = []
        for p in enajenantes:
            percentages.append(p.porcentaje)
            n, pat, mat = _split_name_if_needed(p.nombre, p.apellido_paterno, p.apellido_materno)

            if not pat:
                 raise ValueError(f"Apellido Paterno is required for Enajenante Copropietario: {p.nombre}")
            if not p.curp:
                 raise ValueError(f"CURP is required for Enajenante Copropietario: {p.nombre}")

            cop_list.append(SatDatosEnajenanteCopSC(
                nombre=n,
                apellido_paterno=pat,
                apellido_materno=mat,
                rfc=p.rfc,
                curp=p.curp,
                porcentaje=p.porcentaje
            ))

        validate_copropiedad(percentages)

        return SatDatosEnajenante(
            copro_soc_conyugal_e="Si",
            datos_enajenantes_cop_sc=cop_list
        )

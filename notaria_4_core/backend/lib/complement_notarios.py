from datetime import datetime
from decimal import Decimal
from typing import List, Dict, Any, Tuple
from satcfdi.create.cfd.notariospublicos10 import (
    NotariosPublicos, DescInmueble, DatosOperacion, DatosNotario,
    DatosAdquiriente, DatosUnAdquiriente, DatosAdquirienteCopSC,
    DatosEnajenante, DatosUnEnajenante, DatosEnajenanteCopSC
)
from lib.api_models import ComplementoNotariosModel, DatosAdquiriente as ApiDatosAdquiriente, DatosEnajenante as ApiDatosEnajenante
from lib.fiscal_engine import sanitize_name

def split_name(full_name: str) -> Tuple[str, str, str]:
    """
    Splits a full name into (nombre, apellido_paterno, apellido_materno).
    Returns (full_name, '', '') when a single word input is provided to avoid ambiguous surname assignments.
    """
    parts = full_name.strip().split()
    if len(parts) == 0:
        return "", "", ""
    if len(parts) == 1:
        return parts[0], "", ""
    if len(parts) == 2:
        return parts[0], parts[1], ""

    # Assume the first part is the first name, the second to last is paternal, and last is maternal
    # More complex logic could be needed for multiple names, but this matches common simple heuristics.
    # Alternatively, use all but last two as names.
    nombres = " ".join(parts[:-2])
    paterno = parts[-2]
    materno = parts[-1]
    return nombres, paterno, materno

def create_complemento_notarios(data: ComplementoNotariosModel) -> NotariosPublicos:
    """
    Creates the NotariosPublicos complement from Pydantic model data.
    """
    # Validate date
    fecha = datetime.strptime(data.datos_operacion.fecha_inst_notarial, "%Y-%m-%dT%H:%M:%S")
    if fecha > datetime.now():
        raise ValueError("FechaInstNotarial cannot be in the future.")

    # 1. DescInmuebles
    desc_inmuebles_list = []
    for inm in data.desc_inmuebles:
        inm_dict = {
            "tipo_inmueble": inm.tipo_inmueble,
            "calle": inm.calle,
            "municipio": inm.municipio,
            "estado": inm.estado,
                "pais": inm.pais,
            "codigo_postal": inm.codigo_postal
        }
        if inm.no_exterior: inm_dict["no_exterior"] = inm.no_exterior
        if inm.no_interior: inm_dict["no_interior"] = inm.no_interior
        if inm.colonia: inm_dict["colonia"] = inm.colonia
        if inm.localidad: inm_dict["localidad"] = inm.localidad
        if inm.referencia: inm_dict["referencia"] = inm.referencia
        desc_inmuebles_list.append(DescInmueble(**inm_dict))

    # 2. DatosOperacion
    datos_operacion = DatosOperacion(
        num_instrumento_notarial=data.datos_operacion.num_instrumento_notarial,
        fecha_inst_notarial=data.datos_operacion.fecha_inst_notarial,
        monto_operacion=data.datos_operacion.monto_operacion,
        subtotal=data.datos_operacion.subtotal,
        iva=data.datos_operacion.iva
    )

    # 3. DatosNotario
    # Use defaults if not provided, hardcoded for Notaria 4
    if data.datos_notario:
        curp = data.datos_notario.curp
    else:
        curp = "TOSR520601HOCMXA00"

    datos_notario = DatosNotario(
        curp=curp,
        num_notaria=4,
        entidad_federativa="06",
        adscripcion="MANZANILLO, COLIMA"
    )

    # Helper function to construct Adquiriente/Enajenante nodes
    def build_datos_party(
        parties: List[Any],
        is_adquiriente: bool
    ):
        if not parties:
            return None

        copro_e = parties[0].copro_soc_conyugal_e

        # Enforce strict validation: if 'No', list must contain exactly one item
        if copro_e == "No" and len(parties) != 1:
            raise ValueError(f"If CoproSocConyugalE is 'No', exactly one {'Adquiriente' if is_adquiriente else 'Enajenante'} must be provided.")

        if copro_e == "Si":
            total_pct = sum([p.porcentaje for p in parties if p.porcentaje is not None])
            if total_pct != Decimal("100.00"):
                raise ValueError(f"Sum of percentages in {'Adquirientes' if is_adquiriente else 'Enajenantes'} coproperty must be 100.00%, got {total_pct}")

        if is_adquiriente:
            if copro_e == "No":
                party = parties[0]
                n, p, m = party.nombre, party.apellido_paterno, party.apellido_materno
                if not p and not m:
                    n, p, m = split_name(sanitize_name(n))
                else:
                    n = sanitize_name(n)
                    if p: p = sanitize_name(p)
                    if m: m = sanitize_name(m)

                un_adquiriente = DatosUnAdquiriente(
                    nombre=n, rfc=party.rfc, curp=party.curp,
                    apellido_paterno=p if p else None,
                    apellido_materno=m if m else None
                )
                return DatosAdquiriente(
                    copro_soc_conyugal_e="No",
                    datos_un_adquiriente=un_adquiriente
                )
            else:
                cop_sc_list = []
                for party in parties:
                    n, p, m = party.nombre, party.apellido_paterno, party.apellido_materno
                    if not p and not m:
                        n, p, m = split_name(sanitize_name(n))
                    else:
                        n = sanitize_name(n)
                        if p: p = sanitize_name(p)
                        if m: m = sanitize_name(m)

                    cop_sc = DatosAdquirienteCopSC(
                        nombre=n, rfc=party.rfc, curp=party.curp, porcentaje=party.porcentaje,
                        apellido_paterno=p if p else None,
                        apellido_materno=m if m else None
                    )
                    cop_sc_list.append(cop_sc)
                return DatosAdquiriente(
                    copro_soc_conyugal_e="Si",
                    datos_adquirientes_cop_sc=cop_sc_list
                )
        else: # Enajenante
            if copro_e == "No":
                party = parties[0]
                n, p, m = party.nombre, party.apellido_paterno, party.apellido_materno
                if not p and not m:
                    n, p, m = split_name(sanitize_name(n))
                else:
                    n = sanitize_name(n)
                    if p: p = sanitize_name(p)
                    if m: m = sanitize_name(m)

                # Curp is mandatory in XML schema for enajenante in satcfdi v4
                if not party.curp:
                    raise ValueError("CURP is mandatory for Enajenantes.")

                un_enajenante = DatosUnEnajenante(
                    nombre=n, rfc=party.rfc, curp=party.curp,
                    apellido_paterno=p if p else None,
                    apellido_materno=m if m else None
                )
                return DatosEnajenante(
                    copro_soc_conyugal_e="No",
                    datos_un_enajenante=un_enajenante
                )
            else:
                cop_sc_list = []
                for party in parties:
                    n, p, m = party.nombre, party.apellido_paterno, party.apellido_materno
                    if not p and not m:
                        n, p, m = split_name(sanitize_name(n))
                    else:
                        n = sanitize_name(n)
                        if p: p = sanitize_name(p)
                        if m: m = sanitize_name(m)

                    if not party.curp:
                        raise ValueError("CURP is mandatory for Enajenantes.")

                    cop_sc = DatosEnajenanteCopSC(
                        nombre=n, rfc=party.rfc, curp=party.curp, porcentaje=party.porcentaje,
                        apellido_paterno=p if p else None,
                        apellido_materno=m if m else None
                    )
                    cop_sc_list.append(cop_sc)
                return DatosEnajenante(
                    copro_soc_conyugal_e="Si",
                    datos_enajenantes_cop_sc=cop_sc_list
                )

    datos_adquiriente = build_datos_party(data.datos_adquirientes, is_adquiriente=True)
    datos_enajenante = build_datos_party(data.datos_enajenantes, is_adquiriente=False)

    return NotariosPublicos(
        desc_inmuebles=desc_inmuebles_list,
        datos_operacion=datos_operacion,
        datos_notario=datos_notario,
        datos_adquiriente=datos_adquiriente,
        datos_enajenante=datos_enajenante
    )

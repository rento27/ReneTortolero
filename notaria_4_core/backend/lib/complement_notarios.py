from decimal import Decimal
from typing import List, Dict, Any, Tuple
from datetime import datetime
from .api_models import ComplementoNotariosModel, DatosAdquiriente, DatosEnajenante, DescInmueble
from .fiscal_engine import sanitize_name

try:
    from satcfdi.create.cfd import notariospublicos10
except ImportError:
    notariospublicos10 = None

def split_name(full_name: str) -> Tuple[str, str, str]:
    """
    Returns a 3-tuple (nombre, apellido_paterno, apellido_materno).
    Returns (full_name, '', '') when a single word input is provided to avoid ambiguous surname assignments.
    """
    parts = full_name.strip().split()
    if len(parts) <= 1:
        return (full_name, "", "")

    # A simple heuristic: the last two words are paternal and maternal surnames
    # The rest is the first name.
    if len(parts) == 2:
        return (parts[0], parts[1], "")

    apellido_materno = parts[-1]
    apellido_paterno = parts[-2]
    nombre = " ".join(parts[:-2])
    return (nombre, apellido_paterno, apellido_materno)

def _build_adquiriente(adquirientes: List[DatosAdquiriente], copro_soc_conyugal_a: str):
    if copro_soc_conyugal_a == "No":
        if len(adquirientes) != 1:
            raise ValueError("Exactly one adquiriente required when copro_soc_conyugal_a is 'No'.")

        adq = adquirientes[0]
        sanitized_name = sanitize_name(adq.nombre)
        if adq.apellido_paterno is not None or adq.apellido_materno is not None:
            nombre = sanitized_name
            paterno = adq.apellido_paterno or ""
            materno = adq.apellido_materno or ""
        else:
            nombre, paterno, materno = split_name(sanitized_name)

        datos_un = notariospublicos10.DatosUnAdquiriente(
            nombre=nombre,
            apellido_paterno=paterno,
            apellido_materno=materno,
            rfc=adq.rfc,
            curp=adq.curp
        )
        return notariospublicos10.DatosAdquiriente(
            copro_soc_conyugal_e=copro_soc_conyugal_a,
            datos_un_adquiriente=datos_un
        )
    else:
        # copro_soc_conyugal_a == 'Si'
        total_percent = Decimal("0.00")
        cop_list = []
        for adq in adquirientes:
            sanitized_name = sanitize_name(adq.nombre)
            if adq.apellido_paterno is not None or adq.apellido_materno is not None:
                nombre = sanitized_name
                paterno = adq.apellido_paterno or ""
                materno = adq.apellido_materno or ""
            else:
                nombre, paterno, materno = split_name(sanitized_name)

            porcentaje = adq.porcentaje if adq.porcentaje is not None else Decimal("0.00")
            total_percent += porcentaje

            cop_list.append(notariospublicos10.DatosAdquirienteCopSC(
                nombre=nombre,
                apellido_paterno=paterno,
                apellido_materno=materno,
                rfc=adq.rfc,
                curp=adq.curp,
                porcentaje=porcentaje
            ))

        if total_percent != Decimal("100.00"):
            raise ValueError(f"Sum of percentages for adquirientes must be exactly 100.00%, got {total_percent}")

        return notariospublicos10.DatosAdquiriente(
            copro_soc_conyugal_e=copro_soc_conyugal_a,
            datos_adquirientes_cop_sc=cop_list
        )

def _build_enajenante(enajenantes: List[DatosEnajenante], copro_soc_conyugal_e: str):
    if copro_soc_conyugal_e == "No":
        if len(enajenantes) != 1:
            raise ValueError("Exactly one enajenante required when copro_soc_conyugal_e is 'No'.")

        enaj = enajenantes[0]
        if not enaj.curp:
            raise ValueError("CURP is mandatory for DatosEnajenante in XML schema.")

        sanitized_name = sanitize_name(enaj.nombre)
        if enaj.apellido_paterno is not None or enaj.apellido_materno is not None:
            nombre = sanitized_name
            paterno = enaj.apellido_paterno or ""
            materno = enaj.apellido_materno or ""
        else:
            nombre, paterno, materno = split_name(sanitized_name)

        datos_un = notariospublicos10.DatosUnEnajenante(
            nombre=nombre,
            apellido_paterno=paterno,
            apellido_materno=materno,
            rfc=enaj.rfc,
            curp=enaj.curp
        )
        return notariospublicos10.DatosEnajenante(
            copro_soc_conyugal_e=copro_soc_conyugal_e,
            datos_un_enajenante=datos_un
        )
    else:
        # copro_soc_conyugal_e == 'Si'
        total_percent = Decimal("0.00")
        cop_list = []
        for enaj in enajenantes:
            if not enaj.curp:
                raise ValueError("CURP is mandatory for DatosEnajenante in XML schema.")

            sanitized_name = sanitize_name(enaj.nombre)
            if enaj.apellido_paterno is not None or enaj.apellido_materno is not None:
                nombre = sanitized_name
                paterno = enaj.apellido_paterno or ""
                materno = enaj.apellido_materno or ""
            else:
                nombre, paterno, materno = split_name(sanitized_name)

            porcentaje = enaj.porcentaje if enaj.porcentaje is not None else Decimal("0.00")
            total_percent += porcentaje

            cop_list.append(notariospublicos10.DatosEnajenanteCopSC(
                nombre=nombre,
                apellido_paterno=paterno,
                apellido_materno=materno,
                rfc=enaj.rfc,
                curp=enaj.curp,
                porcentaje=porcentaje
            ))

        if total_percent != Decimal("100.00"):
            raise ValueError(f"Sum of percentages for enajenantes must be exactly 100.00%, got {total_percent}")

        return notariospublicos10.DatosEnajenante(
            copro_soc_conyugal_e=copro_soc_conyugal_e,
            datos_enajenantes_cop_sc=cop_list
        )

def create_complemento_notarios(data: ComplementoNotariosModel) -> Any:
    """
    Creates the NotariosPublicos complement from the provided model data.
    """
    if not notariospublicos10:
        raise ImportError("satcfdi library is required for create_complemento_notarios.")

    # 1. Validate FechaInstNotarial is not in the future and strictly formatted
    # Format expected: YYYY-MM-DD
    try:
        fecha_inst = datetime.strptime(data.datos_operacion.fecha_inst_notarial, "%Y-%m-%d").date()
        if fecha_inst > datetime.now().date():
            raise ValueError("FechaInstNotarial cannot be in the future.")
    except ValueError as ve:
        if "time data" in str(ve):
            raise ValueError(f"FechaInstNotarial must be in YYYY-MM-DD format. Got: {data.datos_operacion.fecha_inst_notarial}")
        else:
            raise ve

    # 2. Build DatosNotario (Constants fallback if not provided)
    if not data.datos_notario:
        raise ValueError("datos_notario must be provided.")

    datos_notario = notariospublicos10.DatosNotario(
        curp=data.datos_notario.curp,
        num_notaria=data.datos_notario.num_notaria,
        entidad_federativa=data.datos_notario.entidad_federativa,
        adscripcion=data.datos_notario.adscripcion
    )

    # 3. Build DatosOperacion
    datos_operacion = notariospublicos10.DatosOperacion(
        num_instrumento_notarial=data.datos_operacion.num_instrumento_notarial,
        fecha_inst_notarial=data.datos_operacion.fecha_inst_notarial,
        monto_operacion=data.datos_operacion.monto_operacion,
        subtotal=data.datos_operacion.subtotal,
        iva=data.datos_operacion.iva
    )

    # 4. Build DescInmuebles
    desc_inmuebles = []
    for inm in data.desc_inmuebles:
        desc_inmuebles.append(notariospublicos10.DescInmueble(
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
        ))

    # 5. Build DatosAdquiriente
    datos_adquiriente = _build_adquiriente(data.datos_adquiriente, data.copro_soc_conyugal_a)

    # 6. Build DatosEnajenante
    datos_enajenante = _build_enajenante(data.datos_enajenante, data.copro_soc_conyugal_e)

    # 7. Build and return NotariosPublicos complement
    comp = notariospublicos10.NotariosPublicos(
        desc_inmuebles=desc_inmuebles,
        datos_operacion=datos_operacion,
        datos_notario=datos_notario,
        datos_enajenante=datos_enajenante,
        datos_adquiriente=datos_adquiriente
    )
    return comp

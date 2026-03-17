from decimal import Decimal
import datetime
from typing import List, Tuple

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
    if len(parts) == 1:
        return parts[0], "", ""
    elif len(parts) == 2:
        return parts[0], parts[1], ""
    else:
        # Assuming the last two words are the surnames, and everything else is the name.
        nombre = " ".join(parts[:-2])
        return nombre, parts[-2], parts[-1]

def create_complemento_notarios(comp_data: 'ComplementoNotariosModel') -> 'notariospublicos10.NotariosPublicos':
    """
    Creates the NotariosPublicos complement from the provided Pydantic model representation.
    Hardcodes Notaria 4 constants.
    Validates rules based on CoproSocConyugalE, Date, and Percentages.
    """
    if not notariospublicos10:
        raise ImportError("satcfdi library is required to create NotariosPublicos complement.")

    # Validate FechaInstNotarial is not in the future
    fecha_inst = datetime.datetime.fromisoformat(comp_data.datos_operacion.fecha_inst_notarial)
    if fecha_inst > datetime.datetime.now(datetime.timezone.utc).replace(tzinfo=None):
        raise ValueError("FechaInstNotarial cannot be in the future.")

    # Validation: coproperty percentages
    def validate_coproperty(parties: list, type_str: str):
        if not parties:
            return

        copro_val = parties[0].copro_soc_conyugal_e

        if copro_val == 'No' and len(parties) != 1:
            raise ValueError(f"If CoproSocConyugalE is 'No', there must be exactly one {type_str}.")

        if copro_val == 'Si':
            total_pct = sum([p.porcentaje for p in parties if p.porcentaje is not None])
            if total_pct != Decimal("100.00"):
                raise ValueError(f"Sum of percentages for {type_str} must be exactly 100.00%, got {total_pct}")

    validate_coproperty(comp_data.datos_adquiriente, "Adquiriente")
    validate_coproperty(comp_data.datos_enajenante, "Enajenante")

    # Build Adquiriente
    adquiriente_wrapper = None
    if comp_data.datos_adquiriente:
        copro_val = comp_data.datos_adquiriente[0].copro_soc_conyugal_e
        if copro_val == 'No':
            p = comp_data.datos_adquiriente[0]
            nombre = p.nombre
            apaterno = p.apellido_paterno
            amaterno = p.apellido_materno
            if not apaterno and not amaterno:
                nombre, apaterno, amaterno = split_name(p.nombre)

            adquiriente_wrapper = notariospublicos10.DatosUnAdquiriente(
                nombre=nombre,
                apellido_paterno=apaterno,
                apellido_materno=amaterno,
                rfc=p.rfc,
                curp=p.curp
            )
        else:
            cop_sc_list = []
            for p in comp_data.datos_adquiriente:
                nombre = p.nombre
                apaterno = p.apellido_paterno
                amaterno = p.apellido_materno
                if not apaterno and not amaterno:
                    nombre, apaterno, amaterno = split_name(p.nombre)

                cop_sc_list.append(notariospublicos10.DatosAdquirienteCopSC(
                    nombre=nombre,
                    apellido_paterno=apaterno,
                    apellido_materno=amaterno,
                    rfc=p.rfc,
                    curp=p.curp,
                    porcentaje=p.porcentaje
                ))
            adquiriente_wrapper = cop_sc_list

    datos_adquiriente_node = notariospublicos10.DatosAdquiriente(
        copro_soc_conyugal_e=comp_data.datos_adquiriente[0].copro_soc_conyugal_e if comp_data.datos_adquiriente else 'No',
        datos_un_adquiriente=adquiriente_wrapper if type(adquiriente_wrapper) is not list else None,
        datos_adquirientes_cop_sc=adquiriente_wrapper if type(adquiriente_wrapper) is list else None
    )


    # Build Enajenante
    enajenante_wrapper = None
    if comp_data.datos_enajenante:
        copro_val = comp_data.datos_enajenante[0].copro_soc_conyugal_e
        if copro_val == 'No':
            p = comp_data.datos_enajenante[0]
            nombre = p.nombre
            apaterno = p.apellido_paterno
            amaterno = p.apellido_materno
            if not apaterno and not amaterno:
                nombre, apaterno, amaterno = split_name(p.nombre)

            enajenante_wrapper = notariospublicos10.DatosUnEnajenante(
                nombre=nombre,
                apellido_paterno=apaterno,
                apellido_materno=amaterno,
                rfc=p.rfc,
                curp=p.curp
            )
        else:
            cop_sc_list = []
            for p in comp_data.datos_enajenante:
                nombre = p.nombre
                apaterno = p.apellido_paterno
                amaterno = p.apellido_materno
                if not apaterno and not amaterno:
                    nombre, apaterno, amaterno = split_name(p.nombre)

                cop_sc_list.append(notariospublicos10.DatosEnajenanteCopSC(
                    nombre=nombre,
                    apellido_paterno=apaterno,
                    apellido_materno=amaterno,
                    rfc=p.rfc,
                    curp=p.curp,
                    porcentaje=p.porcentaje
                ))
            enajenante_wrapper = cop_sc_list

    datos_enajenante_node = notariospublicos10.DatosEnajenante(
        copro_soc_conyugal_e=comp_data.datos_enajenante[0].copro_soc_conyugal_e if comp_data.datos_enajenante else 'No',
        datos_un_enajenante=enajenante_wrapper if type(enajenante_wrapper) is not list else None,
        datos_enajenantes_cop_sc=enajenante_wrapper if type(enajenante_wrapper) is list else None
    )

    # Build DescInmuebles
    desc_inmuebles_list = []
    for inm in comp_data.desc_inmuebles:
        desc_inmuebles_list.append(notariospublicos10.DescInmueble(
            tipo_inmueble=inm.tipo_inmueble,
            calle=inm.calle,
            estado=inm.estado,
            codigo_postal=inm.codigo_postal
        ))

    # Build Complement
    return notariospublicos10.NotariosPublicos(
        desc_inmuebles=desc_inmuebles_list,
        datos_operacion=notariospublicos10.DatosOperacion(
            num_instrumento_notarial=comp_data.datos_operacion.num_instrumento_notarial,
            fecha_inst_notarial=comp_data.datos_operacion.fecha_inst_notarial,
            monto_operacion=comp_data.datos_operacion.monto_operacion,
            subtotal=comp_data.datos_operacion.subtotal,
            iva=comp_data.datos_operacion.iva
        ),
        datos_notario=notariospublicos10.DatosNotario(
            curp=comp_data.datos_notario.curp,
            num_notaria=comp_data.datos_notario.num_notaria,
            entidad_federativa=comp_data.datos_notario.entidad_federativa,
            adscripcion=comp_data.datos_notario.adscripcion
        ),
        datos_adquiriente=datos_adquiriente_node,
        datos_enajenante=datos_enajenante_node
    )

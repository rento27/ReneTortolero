import datetime
from decimal import Decimal
from typing import List, Tuple
from satcfdi.create.cfd import notariospublicos10
from .api_models import ComplementoNotariosModel, DatosAdquiriente, DatosEnajenante, DescInmueble

def split_name(full_name: str) -> Tuple[str, str, str]:
    """
    Splits a full name into (nombre, apellido_paterno, apellido_materno).
    Returns (full_name, '', '') when a single word input is provided to avoid ambiguous surname assignments.
    """
    parts = full_name.split()
    if len(parts) == 1:
        return full_name, '', ''
    elif len(parts) == 2:
        return parts[0], parts[1], ''
    elif len(parts) >= 3:
        return ' '.join(parts[:-2]), parts[-2], parts[-1]
    return '', '', ''

def create_complemento_notarios(data: ComplementoNotariosModel) -> notariospublicos10.NotariosPublicos:
    """
    Constructs the NotariosPublicos complement from the provided model.
    Applies strict validations:
    - exact YYYY-MM-DD date format
    - 100.00% sum for co-owners percentages
    - Map correctly to DatosAdquirienteCopSC and DatosEnajenanteCopSC inside wrappers,
      or DatosUnAdquiriente and DatosUnEnajenante if copro_soc_conyugal_e is 'No', ensuring singular lists when 'No'.
    """
    # Exact YYYY-MM-DD date format
    try:
        datetime.datetime.strptime(data.datos_operacion.fecha_inst_notarial, "%Y-%m-%d")
    except ValueError:
        raise ValueError("Invalid fecha_inst_notarial format. Expected YYYY-MM-DD")

    # 100.00% sum for co-owners percentages
    adquiriente_copro = any(a.copro_soc_conyugal_e == 'Si' for a in data.datos_adquiriente)
    if adquiriente_copro:
        total = sum((a.porcentaje or Decimal(0)) for a in data.datos_adquiriente)
        if total != Decimal('100.00'):
            raise ValueError(f"Sum of adquiriente copropiedad percentages must be 100.00%, got {total}")
    else:
        if len(data.datos_adquiriente) != 1:
            raise ValueError("When CoproSocConyugalE is 'No', datos_adquiriente must contain exactly one item.")

    enajenante_copro = any(e.copro_soc_conyugal_e == 'Si' for e in data.datos_enajenante)
    if enajenante_copro:
        total = sum((e.porcentaje or Decimal(0)) for e in data.datos_enajenante)
        if total != Decimal('100.00'):
            raise ValueError(f"Sum of enajenante copropiedad percentages must be 100.00%, got {total}")
    else:
        if len(data.datos_enajenante) != 1:
            raise ValueError("When CoproSocConyugalE is 'No', datos_enajenante must contain exactly one item.")

    # Convert DescInmuebles
    desc_inmuebles = [
        notariospublicos10.DescInmueble(
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

    # Convert DatosOperacion
    datos_operacion = notariospublicos10.DatosOperacion(
        num_instrumento_notarial=data.datos_operacion.num_instrumento_notarial,
        fecha_inst_notarial=data.datos_operacion.fecha_inst_notarial,
        monto_operacion=data.datos_operacion.monto_operacion,
        subtotal=data.datos_operacion.subtotal,
        iva=data.datos_operacion.iva
    )

    # Adquirientes
    if adquiriente_copro:
        cop_sc = []
        for a in data.datos_adquiriente:
            n, p, m = a.nombre, a.apellido_paterno, a.apellido_materno
            if not p and not m:
                n, p, m = split_name(a.nombre)
            cop_sc.append(notariospublicos10.DatosAdquirienteCopSC(
                nombre=n,
                apellido_paterno=p,
                apellido_materno=m,
                rfc=a.rfc,
                curp=a.curp,
                porcentaje=a.porcentaje
            ))
        datos_adquiriente = notariospublicos10.DatosAdquirientes(
            copro_soc_conyugal_e='Si',
            datos_adquirientes_cop_sc=cop_sc
        )
    else:
        a = data.datos_adquiriente[0]
        n, p, m = a.nombre, a.apellido_paterno, a.apellido_materno
        if not p and not m:
            n, p, m = split_name(a.nombre)
        datos_adquiriente = notariospublicos10.DatosAdquirientes(
            copro_soc_conyugal_e='No',
            datos_un_adquiriente=notariospublicos10.DatosUnAdquiriente(
                nombre=n,
                apellido_paterno=p,
                apellido_materno=m,
                rfc=a.rfc,
                curp=a.curp
            )
        )

    # Enajenantes
    if enajenante_copro:
        cop_sc = []
        for e in data.datos_enajenante:
            n, p, m = e.nombre, e.apellido_paterno, e.apellido_materno
            if not p and not m:
                n, p, m = split_name(e.nombre)
            cop_sc.append(notariospublicos10.DatosEnajenanteCopSC(
                nombre=n,
                apellido_paterno=p,
                apellido_materno=m,
                rfc=e.rfc,
                curp=e.curp,
                porcentaje=e.porcentaje
            ))
        datos_enajenante = notariospublicos10.DatosEnajenantes(
            copro_soc_conyugal_e='Si',
            datos_enajenantes_cop_sc=cop_sc
        )
    else:
        e = data.datos_enajenante[0]
        n, p, m = e.nombre, e.apellido_paterno, e.apellido_materno
        if not p and not m:
            n, p, m = split_name(e.nombre)
        datos_enajenante = notariospublicos10.DatosEnajenantes(
            copro_soc_conyugal_e='No',
            datos_un_enajenante=notariospublicos10.DatosUnEnajenante(
                nombre=n,
                apellido_paterno=p,
                apellido_materno=m,
                rfc=e.rfc,
                curp=e.curp
            )
        )

    return notariospublicos10.NotariosPublicos(
        desc_inmuebles=desc_inmuebles,
        datos_operacion=datos_operacion,
        datos_notario=notariospublicos10.DatosNotario(
            curp=data.datos_notario.curp,
            num_notaria=data.datos_notario.num_notaria,
            entidad_federativa=data.datos_notario.entidad_federativa,
            adscripcion=data.datos_notario.adscripcion
        ),
        datos_adquiriente=datos_adquiriente,
        datos_enajenante=datos_enajenante
    )

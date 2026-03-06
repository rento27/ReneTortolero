from datetime import date
from decimal import Decimal
from satcfdi.create.cfd import notariospublicos10 as np10

def split_name(full_name: str):
    parts = full_name.split()
    if len(parts) == 1:
        return '', ''
    elif len(parts) == 2:
        return parts[1], ''
    else:
        return parts[-2], parts[-1]

def create_complemento_notarios(data: 'ComplementoNotariosModel') -> np10.NotariosPublicos:
    # Validate FechaInstNotarial is not in the future
    if data.datos_operacion.fecha_inst_notarial > date.today():
        raise ValueError("FechaInstNotarial cannot be in the future")

    # Hardcoded defaults for Notaria 4
    num_notaria = 4
    entidad_federativa = "06"
    adscripcion = "MANZANILLO, COLIMA"
    curp = "TOSR520601HOCMXA00"
    if data.datos_notario:
        curp = data.datos_notario.curp
        num_notaria = data.datos_notario.num_notaria
        entidad_federativa = data.datos_notario.entidad_federativa
        adscripcion = data.datos_notario.adscripcion

    datos_notario = np10.DatosNotario(
        curp=curp,
        num_notaria=num_notaria,
        entidad_federativa=entidad_federativa,
        adscripcion=adscripcion
    )

    datos_operacion = np10.DatosOperacion(
        num_instrumento_notarial=data.datos_operacion.num_instrumento_notarial,
        fecha_inst_notarial=data.datos_operacion.fecha_inst_notarial,
        monto_operacion=data.datos_operacion.monto_operacion,
        subtotal=data.datos_operacion.subtotal,
        iva=data.datos_operacion.iva
    )

    # Inmuebles
    desc_inmuebles = []
    for inm in data.desc_inmuebles:
        desc_inmuebles.append(np10.DescInmueble(
            tipo_inmueble=inm.tipo_inmueble,
            calle=inm.calle,
            municipio=inm.municipio,
            estado=inm.estado,
            pais=inm.pais,
            codigo_postal=inm.codigo_postal,
            no_exterior=inm.no_exterior,
            no_interior=inm.no_interior,
            colonia=inm.colonia,
            localidad=inm.localidad,
            referencia=inm.referencia
        ))

    # Enajenantes
    datos_enajenante = data.datos_enajenante
    enajenante_cop_sc = None
    enajenante_un = None
    if datos_enajenante:
        if datos_enajenante[0].copro_soc_conyugal_e == 'No':
            if len(datos_enajenante) != 1:
                raise ValueError("If CoproSocConyugalE is 'No', there must be exactly one enajenante")
            e = datos_enajenante[0]
            ap, am = e.apellido_paterno, e.apellido_materno
            if not ap and not am:
                ap, am = split_name(e.nombre)
            enajenante_un = np10.DatosUnEnajenante(
                nombre=e.nombre,
                apellido_paterno=ap,
                apellido_materno=am,
                rfc=e.rfc,
                curp=e.curp
            )
        else:
            sum_perc = Decimal("0")
            cops = []
            for e in datos_enajenante:
                ap, am = e.apellido_paterno, e.apellido_materno
                if not ap and not am:
                    ap, am = split_name(e.nombre)
                perc = e.porcentaje if e.porcentaje is not None else Decimal("0")
                sum_perc += perc
                cops.append(np10.DatosEnajenanteCopSC(
                    nombre=e.nombre,
                    apellido_paterno=ap,
                    apellido_materno=am,
                    rfc=e.rfc,
                    curp=e.curp,
                    porcentaje=perc
                ))
            if sum_perc != Decimal("100.00"):
                raise ValueError(f"Sum of enajenantes percentages must be 100.00%, got {sum_perc}")
            enajenante_cop_sc = cops

    # As per satcfdi, the structure uses `datos_un_enajenante` or `datos_enajenantes_cop_sc` inside DatosEnajenante
    # The actual satcfdi model NP10 has DatosEnajenante class
    datos_enajenante_node = np10.DatosEnajenante(
        copro_soc_conyugal_e=data.datos_enajenante[0].copro_soc_conyugal_e if data.datos_enajenante else 'No',
        datos_un_enajenante=enajenante_un,
        datos_enajenantes_cop_sc=enajenante_cop_sc
    )

    # Adquirientes
    datos_adquiriente = data.datos_adquiriente
    adquiriente_cop_sc = None
    adquiriente_un = None
    if datos_adquiriente:
        if datos_adquiriente[0].copro_soc_conyugal_e == 'No':
            if len(datos_adquiriente) != 1:
                raise ValueError("If CoproSocConyugalE is 'No', there must be exactly one adquiriente")
            a = datos_adquiriente[0]
            ap, am = a.apellido_paterno, a.apellido_materno
            if not ap and not am:
                ap, am = split_name(a.nombre)
            adquiriente_un = np10.DatosUnAdquiriente(
                nombre=a.nombre,
                apellido_paterno=ap,
                apellido_materno=am,
                rfc=a.rfc,
                curp=a.curp
            )
        else:
            sum_perc = Decimal("0")
            cops = []
            for a in datos_adquiriente:
                ap, am = a.apellido_paterno, a.apellido_materno
                if not ap and not am:
                    ap, am = split_name(a.nombre)
                perc = a.porcentaje if a.porcentaje is not None else Decimal("0")
                sum_perc += perc
                cops.append(np10.DatosAdquirienteCopSC(
                    nombre=a.nombre,
                    apellido_paterno=ap,
                    apellido_materno=am,
                    rfc=a.rfc,
                    curp=a.curp,
                    porcentaje=perc
                ))
            if sum_perc != Decimal("100.00"):
                raise ValueError(f"Sum of adquirientes percentages must be 100.00%, got {sum_perc}")
            adquiriente_cop_sc = cops

    datos_adquiriente_node = np10.DatosAdquiriente(
        copro_soc_conyugal_e=data.datos_adquiriente[0].copro_soc_conyugal_e if data.datos_adquiriente else 'No',
        datos_un_adquiriente=adquiriente_un,
        datos_adquirientes_cop_sc=adquiriente_cop_sc
    )

    return np10.NotariosPublicos(
        desc_inmuebles=desc_inmuebles,
        datos_operacion=datos_operacion,
        datos_notario=datos_notario,
        datos_enajenante=datos_enajenante_node,
        datos_adquiriente=datos_adquiriente_node
    )

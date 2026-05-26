from datetime import datetime, date
from decimal import Decimal

# Check for satcfdi availability
try:
    from satcfdi.create.cfd import notariospublicos10
except ImportError:
    notariospublicos10 = None

def split_name(full_name: str, paterno: str = None, materno: str = None) -> tuple:
    """
    Helper to split a full name into (nombre, paterno, materno) if they are not provided separately.
    """
    if paterno or materno:
        return (full_name, paterno or "", materno or "")

    parts = full_name.strip().split()
    if len(parts) == 1:
        return (parts[0], "", "")
    elif len(parts) == 2:
        return (parts[0], parts[1], "")
    elif len(parts) >= 3:
        # Assuming the last two words are the surnames
        return (" ".join(parts[:-2]), parts[-2], parts[-1])
    return (full_name, "", "")

def create_complemento_notarios(complemento_model) -> 'notariospublicos10.NotariosPublicos':
    """
    Constructs the NotariosPublicos complement from a Pydantic model.
    """
    if not notariospublicos10:
        raise RuntimeError("satcfdi module is not available")

    # Validate date
    fecha_inst = complemento_model.fecha_inst_notarial
    if len(fecha_inst) != 10 or fecha_inst[4] != '-' or fecha_inst[7] != '-':
        raise ValueError(f"fecha_inst_notarial must be in YYYY-MM-DD format, got '{fecha_inst}'")

    # Try parsing the date strictly to ensure it's a valid calendar date
    try:
        parsed_date = datetime.strptime(fecha_inst, "%Y-%m-%d").date()
    except ValueError as e:
        raise ValueError(f"Invalid date for fecha_inst_notarial: {e}")

    if parsed_date > date.today():
        raise ValueError(f"fecha_inst_notarial cannot be a future date: {fecha_inst}")

    # Build Inmuebles
    desc_inmuebles = []
    for inmueble in complemento_model.desc_inmuebles:
        desc_inmuebles.append(
            notariospublicos10.DescInmueble(
                tipo_inmueble=inmueble.tipo_inmueble,
                calle=inmueble.calle,
                estado=inmueble.estado,
                municipio=inmueble.municipio,
                pais=inmueble.pais,
                codigo_postal=inmueble.codigo_postal
            )
        )

    # Process Adquirientes
    adquiriente_cop_sc_list = []
    un_adquiriente = None
    adquiriente_sum_percentages = Decimal("0.0")

    for adq in complemento_model.datos_adquirientes:
        nombre, paterno, materno = split_name(adq.nombre, adq.apellido_paterno, adq.apellido_materno)
        if adq.copro_soc_conyugal_e == 'Si':
            # Create DatosAdquirientesCopSC object
            adquiriente_cop_sc_list.append(
                notariospublicos10.DatosAdquirientesCopSC(
                    nombre=nombre,
                    apellido_paterno=paterno,
                    apellido_materno=materno,
                    rfc=adq.rfc,
                    curp=adq.curp,
                    porcentaje=adq.porcentaje
                )
            )
            if adq.porcentaje is not None:
                adquiriente_sum_percentages += Decimal(str(adq.porcentaje))
        else:
            un_adquiriente = notariospublicos10.DatosUnAdquiriente(
                nombre=nombre,
                apellido_paterno=paterno,
                apellido_materno=materno,
                rfc=adq.rfc,
                curp=adq.curp
            )

    if adquiriente_cop_sc_list and adquiriente_sum_percentages != Decimal("100.00"):
        raise ValueError(f"Sum of adquiriente coproperty percentages must be exactly 100.00%, got {adquiriente_sum_percentages:.2f}%")

    if adquiriente_cop_sc_list:
        datos_adquiriente = notariospublicos10.DatosAdquiriente(
            copro_soc_conyugal_e='Si',
            datos_adquirientes_cop_sc=adquiriente_cop_sc_list
        )
    else:
        datos_adquiriente = notariospublicos10.DatosAdquiriente(
            copro_soc_conyugal_e='No',
            datos_un_adquiriente=un_adquiriente
        )

    # Process Enajenantes
    enajenante_cop_sc_list = []
    un_enajenante = None
    enajenante_sum_percentages = Decimal("0.0")

    for ena in complemento_model.datos_enajenantes:
        if not ena.curp:
            raise ValueError("CURP is mandatory for DatosEnajenante")

        nombre, paterno, materno = split_name(ena.nombre, ena.apellido_paterno, ena.apellido_materno)
        if ena.copro_soc_conyugal_e == 'Si':
            enajenante_cop_sc_list.append(
                notariospublicos10.DatosEnajenantesCopSC(
                    nombre=nombre,
                    apellido_paterno=paterno,
                    apellido_materno=materno,
                    rfc=ena.rfc,
                    curp=ena.curp,
                    porcentaje=ena.porcentaje
                )
            )
            if ena.porcentaje is not None:
                enajenante_sum_percentages += Decimal(str(ena.porcentaje))
        else:
            un_enajenante = notariospublicos10.DatosUnEnajenante(
                nombre=nombre,
                apellido_paterno=paterno,
                apellido_materno=materno,
                rfc=ena.rfc,
                curp=ena.curp
            )

    if enajenante_cop_sc_list and enajenante_sum_percentages != Decimal("100.00"):
        raise ValueError(f"Sum of enajenante coproperty percentages must be exactly 100.00%, got {enajenante_sum_percentages:.2f}%")

    if enajenante_cop_sc_list:
        datos_enajenante = notariospublicos10.DatosEnajenante(
            copro_soc_conyugal_e='Si',
            datos_enajenantes_cop_sc=enajenante_cop_sc_list
        )
    else:
        datos_enajenante = notariospublicos10.DatosEnajenante(
            copro_soc_conyugal_e='No',
            datos_un_enajenante=un_enajenante
        )

    curp_notario = complemento_model.datos_notario.curp if complemento_model.datos_notario else "TOSR520601HOCMXA00"
    num_notaria = complemento_model.datos_notario.num_notaria if complemento_model.datos_notario else 4
    entidad_federativa = complemento_model.datos_notario.entidad_federativa if complemento_model.datos_notario else "06"
    adscripcion = complemento_model.datos_notario.adscripcion if complemento_model.datos_notario else "MANZANILLO COLIMA"

    notario = notariospublicos10.NotariosPublicos(
        desc_inmuebles=desc_inmuebles,
        datos_operacion=notariospublicos10.DatosOperacion(
            num_instrumento_notarial=1,
            fecha_inst_notarial=parsed_date,
            monto_operacion=Decimal('0.00'),
            subtotal=Decimal('0.00'),
            iva=Decimal('0.00')
        ),
        datos_notario=notariospublicos10.DatosNotario(
            curp=curp_notario,
            num_notaria=num_notaria,
            entidad_federativa=entidad_federativa,
            adscripcion=adscripcion
        ),
        datos_enajenante=datos_enajenante,
        datos_adquiriente=datos_adquiriente
    )
    return notario

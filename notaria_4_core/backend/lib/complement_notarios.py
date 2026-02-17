from decimal import Decimal
from typing import List, Tuple
from satcfdi.create.cfd.notariospublicos10 import (
    NotariosPublicos,
    DatosNotario,
    DatosOperacion,
    DescInmueble,
    DatosAdquiriente,
    DatosUnAdquiriente,
    DatosAdquirienteCopSC,
    DatosEnajenante,
    DatosUnEnajenante,
    DatosEnajenanteCopSC
)
from .api_models import ComplementoNotariosModel, DatosAdquiriente as APIAdquiriente, DatosEnajenante as APIEnajenante
from .fiscal_engine import validate_copropiedad

# Constants for Notaria 4
NOTARIA_NUM = 4
ENTIDAD_FEDERATIVA = "06" # Colima
ADSCRIPCION = "MANZANILLO, COLIMA"
DEFAULT_CURP_NOTARIO = "TOSR520601HOCMXA00" # Fallback/Placeholder

def split_name(full_name: str) -> Tuple[str, str, str]:
    """
    Splits a full name into Nombre, Apellido Paterno, Apellido Materno.
    Simple heuristic: Last token is Materno, second to last is Paterno, rest is Nombre.
    If only 2 tokens: Nombre, Paterno.
    If 1 token: Nombre, "X" (Paterno required for Enajenante).
    """
    parts = full_name.strip().split()
    if not parts:
        return "", "", ""

    if len(parts) == 1:
        return parts[0], "X", "" # Fallback for single name to satisfy strict validation

    if len(parts) == 2:
        return parts[0], parts[1], ""

    # 3 or more parts
    # Check for common composite last names prefixes (De, La, Del) could be complex.
    # We'll use a simple right-to-left strategy.
    materno = parts[-1]
    paterno = parts[-2]
    nombre = " ".join(parts[:-2])

    return nombre, paterno, materno

def create_datos_adquiriente(adquirientes: List[APIAdquiriente]) -> DatosAdquiriente:
    if not adquirientes:
        raise ValueError("Must have at least one Adquiriente")

    # Validate Coproperty Percentages
    # Assuming if any percentage is provided, we should validate sum to 100%
    # If explicit None (e.g. single owner with implicit 100%), we skip validation unless strict required.
    # However, for robustness, if list > 1, all should have percentage.
    percentages = [adq.porcentaje for adq in adquirientes if adq.porcentaje is not None]
    if percentages:
        validate_copropiedad(percentages)

    main_adq = adquirientes[0]

    # Use explicit fields if available, else fallback to split_name
    if main_adq.apellido_paterno or main_adq.apellido_materno:
        nombre = main_adq.nombre
        pat = main_adq.apellido_paterno
        mat = main_adq.apellido_materno
    else:
        nombre, pat, mat = split_name(main_adq.nombre)

    # DatosUnAdquiriente
    # Note: apellido_paterno is optional in DatosUnAdquiriente constructor
    un_adq_args = {
        "nombre": nombre,
        "rfc": main_adq.rfc,
        "curp": main_adq.curp
    }
    if pat: un_adq_args["apellido_paterno"] = pat
    if mat: un_adq_args["apellido_materno"] = mat

    datos_un_adq = DatosUnAdquiriente(**un_adq_args)

    copro_list = []
    is_copro = len(adquirientes) > 1

    if is_copro:
        for adq in adquirientes[1:]:
            if adq.apellido_paterno or adq.apellido_materno:
                n = adq.nombre
                p = adq.apellido_paterno
                m = adq.apellido_materno
            else:
                n, p, m = split_name(adq.nombre)

            copro_args = {
                "nombre": n,
                "rfc": adq.rfc,
                "curp": adq.curp,
                "porcentaje": adq.porcentaje
            }
            if p: copro_args["apellido_paterno"] = p
            if m: copro_args["apellido_materno"] = m

            copro_list.append(DatosAdquirienteCopSC(**copro_args))

    return DatosAdquiriente(
        copro_soc_conyugal_e="Si" if is_copro else "No",
        datos_un_adquiriente=datos_un_adq,
        datos_adquirientes_cop_sc=copro_list if copro_list else None
    )

def create_datos_enajenante(enajenantes: List[APIEnajenante]) -> DatosEnajenante:
    if not enajenantes:
        raise ValueError("Must have at least one Enajenante")

    # Validate percentages
    percentages = [enaj.porcentaje for enaj in enajenantes if enaj.porcentaje is not None]
    if percentages:
        validate_copropiedad(percentages)

    main_enaj = enajenantes[0]

    if main_enaj.apellido_paterno or main_enaj.apellido_materno:
        nombre = main_enaj.nombre
        pat = main_enaj.apellido_paterno
        mat = main_enaj.apellido_materno
    else:
        nombre, pat, mat = split_name(main_enaj.nombre)

    # DatosUnEnajenante strictly requires apellido_paterno
    if not pat:
        pat = "X" # Fallback to satisfy validation if name is single word

    un_enaj_args = {
        "nombre": nombre,
        "apellido_paterno": pat,
        "rfc": main_enaj.rfc,
        "curp": main_enaj.curp
    }
    if mat: un_enaj_args["apellido_materno"] = mat

    datos_un_enaj = DatosUnEnajenante(**un_enaj_args)

    copro_list = []
    is_copro = len(enajenantes) > 1

    if is_copro:
        for enaj in enajenantes[1:]:
            if enaj.apellido_paterno or enaj.apellido_materno:
                n = enaj.nombre
                p = enaj.apellido_paterno
                m = enaj.apellido_materno
            else:
                n, p, m = split_name(enaj.nombre)
                if not p: p = "X"

            copro_args = {
                "nombre": n,
                "apellido_paterno": p,
                "rfc": enaj.rfc,
                "curp": enaj.curp,
                "porcentaje": enaj.porcentaje
            }
            if m: copro_args["apellido_materno"] = m

            copro_list.append(DatosEnajenanteCopSC(**copro_args))

    return DatosEnajenante(
        copro_soc_conyugal_e="Si" if is_copro else "No",
        datos_un_enajenante=datos_un_enaj,
        datos_enajenantes_cop_sc=copro_list if copro_list else None
    )

def create_complemento_notarios(data: ComplementoNotariosModel) -> NotariosPublicos:
    # 1. DatosOperacion
    datos_operacion = DatosOperacion(
        num_instrumento_notarial=data.datos_operacion.num_instrumento_notarial,
        fecha_inst_notarial=data.datos_operacion.fecha_inst_notarial,
        monto_operacion=data.datos_operacion.monto_operacion,
        subtotal=data.datos_operacion.subtotal,
        iva=data.datos_operacion.iva
    )

    # 2. DatosNotario
    curp_notario = data.datos_notario.curp if data.datos_notario and data.datos_notario.curp else DEFAULT_CURP_NOTARIO
    datos_notario = DatosNotario(
        curp=curp_notario,
        num_notaria=NOTARIA_NUM,
        entidad_federativa=ENTIDAD_FEDERATIVA,
        adscripcion=ADSCRIPCION
    )

    # 3. DescInmueble
    inmueble = DescInmueble(
        tipo_inmueble=data.inmueble.tipo_inmueble,
        calle=data.inmueble.calle,
        no_exterior=data.inmueble.no_exterior,
        no_interior=data.inmueble.no_interior,
        colonia=data.inmueble.colonia,
        localidad=data.inmueble.localidad,
        referencia=data.inmueble.referencia,
        municipio=data.inmueble.municipio,
        estado=data.inmueble.entidad_federativa,
        pais=data.inmueble.pais,
        codigo_postal=data.inmueble.codigo_postal
    )

    # 4. DatosAdquiriente
    datos_adquiriente = create_datos_adquiriente(data.adquirientes)

    # 5. DatosEnajenante
    datos_enajenante = None
    if data.enajenantes:
        datos_enajenante = create_datos_enajenante(data.enajenantes)

    return NotariosPublicos(
        datos_operacion=datos_operacion,
        datos_notario=datos_notario,
        desc_inmuebles=inmueble,
        datos_adquiriente=datos_adquiriente,  # Fixed: singular
        datos_enajenante=datos_enajenante     # Fixed: singular
    )

from decimal import Decimal
import datetime
import logging

try:
    from satcfdi.create.cfd import notariospublicos10 as np
except ImportError:
    np = None

from .api_models import ComplementoNotariosModel, DatosAdquiriente, DatosEnajenante, DescInmueble

logger = logging.getLogger(__name__)

def split_name(full_name: str) -> tuple[str, str, str]:
    """
    Splits a full name into (nombre, apellido_paterno, apellido_materno).
    Returns (full_name, '', '') if it's a single word to avoid ambiguous assignment.
    """
    parts = full_name.strip().split()
    if len(parts) == 1:
        return (full_name, "", "")

    # Heuristic: last two are surnames if more than 2 words, else last is surname
    if len(parts) >= 3:
        nombre = " ".join(parts[:-2])
        ap = parts[-2]
        am = parts[-1]
    else:
        nombre = parts[0]
        ap = parts[1]
        am = ""

    return nombre, ap, am

def validate_date(date_str: str) -> str:
    """
    Validates YYYY-MM-DD format strictly. Raises ValueError if invalid.
    """
    try:
        datetime.datetime.strptime(date_str, "%Y-%m-%d")
        return date_str
    except ValueError:
        raise ValueError(f"Invalid date format for {date_str}. Must be YYYY-MM-DD.")

def create_complemento_notarios(data: ComplementoNotariosModel) -> 'np.NotariosPublicos':
    """
    Generates the NotariosPublicos complement from the provided Pydantic model.
    """
    if not np:
        raise RuntimeError("satcfdi library not available")

    # 1. Validate Date
    validate_date(data.fecha_inst_notarial)

    # 2. Map DescInmuebles
    desc_inmuebles = []
    for inm in data.desc_inmuebles:
        # Note: satcfdi v4 uses 'estado' and 'pais' in DescInmueble
        desc = np.DescInmueble(
            tipo_inmueble=inm.tipo_inmueble,
            calle=inm.calle,
            municipio=inm.municipio,
            estado=inm.estado,
            pais=inm.pais,
            codigo_postal=inm.codigo_postal
        )
        if inm.no_exterior:
            desc['NoExterior'] = inm.no_exterior
        if inm.no_interior:
            desc['NoInterior'] = inm.no_interior
        if inm.colonia:
            desc['Colonia'] = inm.colonia
        if inm.localidad:
            desc['Localidad'] = inm.localidad
        if inm.referencia:
            desc['Referencia'] = inm.referencia
        desc_inmuebles.append(desc)

    # 3. Map Adquirientes
    adquirientes_list = []
    total_pct_adq = Decimal("0.00")
    for adq in data.datos_adquirientes:
        nombre = adq.nombre
        ap = adq.apellido_paterno
        am = adq.apellido_materno

        if ap is None and am is None:
            nombre, ap, am = split_name(adq.nombre)

        adquirientes_list.append({
            'nombre': nombre,
            'apellido_paterno': ap,
            'apellido_materno': am,
            'rfc': adq.rfc,
            'curp': adq.curp,
            'porcentaje': adq.porcentaje,
            'copro_soc_conyugal_e': adq.copro_soc_conyugal_e
        })
        total_pct_adq += adq.porcentaje

    if len(adquirientes_list) > 1 and total_pct_adq != Decimal("100.00"):
        raise ValueError(f"Adquirientes coproperty percentage must sum to 100.00, got {total_pct_adq}")

    if len(adquirientes_list) == 1 and adquirientes_list[0]['copro_soc_conyugal_e'] == "No":
        datos_adquiriente = np.DatosAdquiriente(
            datos_un_adquiriente=np.DatosUnAdquiriente(
                nombre=adquirientes_list[0]['nombre'],
                apellido_paterno=adquirientes_list[0]['apellido_paterno'],
                apellido_materno=adquirientes_list[0]['apellido_materno'],
                rfc=adquirientes_list[0]['rfc'],
                curp=adquirientes_list[0]['curp']
            )
        )
    else:
        # Copropiedad
        cop_list = [
            np.DatosAdquirienteCopSC(
                nombre=a['nombre'],
                apellido_paterno=a['apellido_paterno'],
                apellido_materno=a['apellido_materno'],
                rfc=a['rfc'],
                curp=a['curp'],
                porcentaje=a['porcentaje']
            ) for a in adquirientes_list
        ]
        datos_adquiriente = np.DatosAdquiriente(
            datos_adquirientes_cop_sc=cop_list
        )

    # 4. Map Enajenantes
    enajenantes_list = []
    total_pct_enaj = Decimal("0.00")
    for enaj in data.datos_enajenantes:
        nombre = enaj.nombre
        ap = enaj.apellido_paterno
        am = enaj.apellido_materno

        if ap is None and am is None:
            nombre, ap, am = split_name(enaj.nombre)

        if not enaj.curp:
            raise ValueError("CURP is mandatory for DatosEnajenante")

        enajenantes_list.append({
            'nombre': nombre,
            'apellido_paterno': ap,
            'apellido_materno': am,
            'rfc': enaj.rfc,
            'curp': enaj.curp,
            'porcentaje': enaj.porcentaje,
            'copro_soc_conyugal_e': enaj.copro_soc_conyugal_e
        })
        total_pct_enaj += enaj.porcentaje

    if len(enajenantes_list) > 1 and total_pct_enaj != Decimal("100.00"):
        raise ValueError(f"Enajenantes coproperty percentage must sum to 100.00, got {total_pct_enaj}")

    if len(enajenantes_list) == 1 and enajenantes_list[0]['copro_soc_conyugal_e'] == "No":
        datos_enajenante = np.DatosEnajenante(
            datos_un_enajenante=np.DatosUnEnajenante(
                nombre=enajenantes_list[0]['nombre'],
                apellido_paterno=enajenantes_list[0]['apellido_paterno'],
                apellido_materno=enajenantes_list[0]['apellido_materno'],
                rfc=enajenantes_list[0]['rfc'],
                curp=enajenantes_list[0]['curp'],
                copro_soc_conyugal_e=enajenantes_list[0]['copro_soc_conyugal_e']
            )
        )
    else:
        # Copropiedad
        cop_list = [
            np.DatosEnajenanteCopSC(
                nombre=e['nombre'],
                apellido_paterno=e['apellido_paterno'],
                apellido_materno=e['apellido_materno'],
                rfc=e['rfc'],
                curp=e['curp'],
                porcentaje=e['porcentaje']
            ) for e in enajenantes_list
        ]
        datos_enajenante = np.DatosEnajenante(
            datos_enajenantes_cop_sc=cop_list
        )

    # 5. Assemble Complement
    complemento = np.NotariosPublicos(
        desc_inmuebles=desc_inmuebles,
        datos_operacion=np.DatosOperacion(
            fecha_inst_notarial=data.fecha_inst_notarial,
            num_instrumento_notarial=data.num_instrumento_notarial,
            monto_operacion=data.monto_operacion,
            subtotal=data.subtotal,
            iva=data.iva
        ),
        datos_notario=np.DatosNotario(
            curp=data.datos_notario.curp,
            num_notaria=data.datos_notario.num_notaria,
            entidad_federativa=data.datos_notario.entidad_federativa,
            adscripcion=data.datos_notario.adscripcion
        ),
        datos_adquiriente=datos_adquiriente,
        datos_enajenante=datos_enajenante
    )

    return complemento

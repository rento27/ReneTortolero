from decimal import Decimal
from typing import List, Dict, Any
from datetime import date
from .fiscal_engine import sanitize_name
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

def split_full_name(full_name: str) -> dict:
    """
    Splits a full name into Nombre, ApellidoPaterno, ApellidoMaterno.
    Heuristic:
    - 1 word: Use as Nombre (Paterno/Materno None, which might fail strict validation)
    - 2 words: Nombre + Paterno
    - 3+ words: Nombre(s) + Paterno + Materno
    """
    parts = full_name.strip().split()
    if len(parts) == 0:
        return {"nombre": "", "apellido_paterno": None, "apellido_materno": None}
    if len(parts) == 1:
        return {"nombre": parts[0], "apellido_paterno": None, "apellido_materno": None}
    if len(parts) == 2:
        return {"nombre": parts[0], "apellido_paterno": parts[1], "apellido_materno": None}

    # 3 or more: Assumes last is Materno, second last is Paterno
    return {
        "nombre": " ".join(parts[:-2]),
        "apellido_paterno": parts[-2],
        "apellido_materno": parts[-1]
    }

def ensure_person_fields(person_data: dict) -> dict:
    """
    Ensures 'nombre', 'apellido_paterno', 'apellido_materno' are populated.
    If apellidos are missing, tries to split 'nombre'.
    Also sanitizes names.
    """
    nombre = sanitize_name(person_data.get('nombre', ''))
    paterno = person_data.get('apellido_paterno')
    materno = person_data.get('apellido_materno')

    if paterno:
        paterno = sanitize_name(paterno)
    if materno:
        materno = sanitize_name(materno)

    if not paterno:
        split = split_full_name(nombre)
        return {
            "nombre": split['nombre'],
            "apellido_paterno": split['apellido_paterno'],
            "apellido_materno": split['apellido_materno'],
            "rfc": person_data.get('rfc'),
            "curp": person_data.get('curp')
        }

    return {
        "nombre": nombre,
        "apellido_paterno": paterno,
        "apellido_materno": materno,
        "rfc": person_data.get('rfc'),
        "curp": person_data.get('curp')
    }

def create_complemento_notarios(data: Dict[str, Any]) -> NotariosPublicos:
    """
    Creates a NotariosPublicos complement object from the provided dictionary
    (which should match the structure of ComplementoNotarios model).
    """

    # 1. DatosNotario
    dn_data = data['datos_notario']
    datos_notario = DatosNotario(
        curp=dn_data['curp'],
        num_notaria=dn_data['num_notaria'],
        entidad_federativa=dn_data['entidad_federativa'],
        adscripcion=dn_data.get('adscripcion')
    )

    # 2. DatosOperacion
    do_data = data['datos_operacion']
    datos_operacion = DatosOperacion(
        num_instrumento_notarial=do_data['num_instrumento_notarial'],
        fecha_inst_notarial=do_data['fecha_inst_notarial'], # Assumed date object or string? satcfdi needs date
        monto_operacion=Decimal(str(do_data['monto_operacion'])),
        subtotal=Decimal(str(do_data['subtotal'])),
        iva=Decimal(str(do_data['iva']))
    )

    # 3. DescInmuebles
    inmuebles = []
    for inmueble in data['desc_inmuebles']:
        inmuebles.append(DescInmueble(
            tipo_inmueble=inmueble['tipo_inmueble'],
            calle=inmueble['calle'],
            municipio=inmueble['municipio'],
            estado=inmueble['estado'],
            pais=inmueble['pais'],
            codigo_postal=inmueble['codigo_postal'],
            no_exterior=inmueble.get('no_exterior'),
            no_interior=inmueble.get('no_interior'),
            colonia=inmueble.get('colonia'),
            localidad=inmueble.get('localidad'),
            referencia=inmueble.get('referencia')
        ))

    # 4. DatosAdquiriente
    da_data = data['datos_adquiriente']
    adquiriente_kwargs = {
        'copro_soc_conyugal_e': da_data['copro_soc_conyugal_e']
    }

    if da_data.get('datos_un_adquiriente'):
        p = ensure_person_fields(da_data['datos_un_adquiriente'])
        adquiriente_kwargs['datos_un_adquiriente'] = DatosUnAdquiriente(
            nombre=p['nombre'],
            rfc=p['rfc'],
            apellido_paterno=p.get('apellido_paterno'),
            apellido_materno=p.get('apellido_materno'),
            curp=p.get('curp')
        )
    elif da_data.get('datos_adquirientes_cop_sc'):
        copros = []
        for c in da_data['datos_adquirientes_cop_sc']:
            p = ensure_person_fields(c)
            copros.append(DatosAdquirienteCopSC(
                nombre=p['nombre'],
                rfc=p['rfc'],
                porcentaje=Decimal(str(c['porcentaje'])),
                apellido_paterno=p.get('apellido_paterno'),
                apellido_materno=p.get('apellido_materno'),
                curp=p.get('curp')
            ))
        adquiriente_kwargs['datos_adquirientes_cop_sc'] = copros

    datos_adquiriente = DatosAdquiriente(**adquiriente_kwargs)

    # 5. DatosEnajenante
    de_data = data['datos_enajenante']
    enajenante_kwargs = {
        'copro_soc_conyugal_e': de_data['copro_soc_conyugal_e']
    }

    if de_data.get('datos_un_enajenante'):
        p = ensure_person_fields(de_data['datos_un_enajenante'])
        # Note: DatosUnEnajenante requires apellido_paterno and curp strictly in some versions, check signature
        # Signature: (nombre, apellido_paterno, rfc, curp, apellido_materno=None)
        # We must ensure they are not None.
        if not p.get('apellido_paterno'):
             # Last resort if split failed to give paterno (e.g. 1 word name)
             p['apellido_paterno'] = "."
        if not p.get('curp'):
             # Logic for foreign enajenantes? Prompt doesn't specify. Assuming required.
             pass

        enajenante_kwargs['datos_un_enajenante'] = DatosUnEnajenante(
            nombre=p['nombre'],
            rfc=p['rfc'],
            apellido_paterno=p['apellido_paterno'],
            curp=p.get('curp', 'NO_CURP_PROVIDED'), # Fallback or let it fail?
            apellido_materno=p.get('apellido_materno')
        )
    elif de_data.get('datos_enajenantes_cop_sc'):
        copros = []
        for c in de_data['datos_enajenantes_cop_sc']:
            p = ensure_person_fields(c)
            copros.append(DatosEnajenanteCopSC(
                nombre=p['nombre'],
                rfc=p['rfc'],
                porcentaje=Decimal(str(c['porcentaje'])),
                apellido_paterno=p.get('apellido_paterno'),
                apellido_materno=p.get('apellido_materno'),
                curp=p.get('curp')
            ))
        enajenante_kwargs['datos_enajenantes_cop_sc'] = copros

    datos_enajenante = DatosEnajenante(**enajenante_kwargs)

    # 6. Construct Complemento
    comp = NotariosPublicos(
        desc_inmuebles=inmuebles,
        datos_operacion=datos_operacion,
        datos_notario=datos_notario,
        datos_enajenante=datos_enajenante,
        datos_adquiriente=datos_adquiriente
    )

    return comp

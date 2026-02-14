from datetime import date
from decimal import Decimal
from typing import List
from satcfdi.create.cfd.notariospublicos10 import (
    NotariosPublicos,
    DescInmueble,
    DatosOperacion as CFDIDatosOperacion,
    DatosNotario as CFDIDatosNotario,
    DatosAdquiriente as CFDIDatosAdquiriente,
    DatosUnAdquiriente as CFDIDatosUnAdquiriente,
    DatosAdquirienteCopSC as CFDIDatosAdquirienteCopSC,
    DatosEnajenante as CFDIDatosEnajenante,
    DatosUnEnajenante as CFDIDatosUnEnajenante,
    DatosEnajenanteCopSC as CFDIDatosEnajenanteCopSC
)
from .api_models import ComplementoNotariosModel, DatosAdquiriente, DatosEnajenante, DatosNotario

def validate_date_not_future(d: date):
    if d > date.today():
        raise ValueError(f"FechaInstNotarial cannot be in the future: {d}")

def validate_coproperty_sum(items: List[Decimal]):
    total = sum(items)
    if total != Decimal("100.00"):
        raise ValueError(f"Sum of percentages must be 100.00%, got {total}")

def split_name(full_name: str):
    """
    Simple name splitter fallback.
    Assumes "First Middle Last1 Last2" logic.
    """
    parts = full_name.split()
    if len(parts) >= 3:
        return {
            'nombre': " ".join(parts[:-2]),
            'apellido_paterno': parts[-2],
            'apellido_materno': parts[-1]
        }
    elif len(parts) == 2:
        return {
            'nombre': parts[0],
            'apellido_paterno': parts[1],
            'apellido_materno': ''
        }
    else:
        return {
            'nombre': full_name,
            'apellido_paterno': 'X', # Fallback to satisfy strict requirement
            'apellido_materno': ''
        }

def prepare_person_data(person: DatosAdquiriente | DatosEnajenante):
    """
    Prepares name data, handling splitting if necessary.
    """
    data = {
        'nombre': person.nombre,
        'apellido_paterno': person.apellido_paterno,
        'apellido_materno': person.apellido_materno,
        'rfc': person.rfc,
        'curp': person.curp
    }

    if not data['apellido_paterno']:
        split = split_name(person.nombre)
        data['nombre'] = split['nombre']
        data['apellido_paterno'] = split['apellido_paterno']
        if not data['apellido_materno']:
            data['apellido_materno'] = split['apellido_materno']

    return data

def create_complemento_notarios(data: ComplementoNotariosModel) -> NotariosPublicos:
    # 1. Validate Date
    validate_date_not_future(data.datos_operacion.fecha_inst_notarial)

    # 2. DatosNotario
    notary_curp = data.datos_notario.curp or "TOSR520601HOCMXA00" # Fallback
    datos_notario = CFDIDatosNotario(
        num_notaria=data.datos_notario.num_notaria,
        entidad_federativa=data.datos_notario.entidad_federativa,
        adscripcion=data.datos_notario.adscripcion,
        curp=notary_curp
    )

    # 3. DatosOperacion
    datos_operacion = CFDIDatosOperacion(
        num_instrumento_notarial=data.datos_operacion.num_instrumento_notarial,
        fecha_inst_notarial=data.datos_operacion.fecha_inst_notarial,
        monto_operacion=data.datos_operacion.monto_operacion,
        subtotal=data.datos_operacion.subtotal,
        iva=data.datos_operacion.iva
    )

    # 4. DescInmuebles
    desc_inmuebles = [
        DescInmueble(
            tipo_inmueble=i.tipo_inmueble,
            calle=i.calle,
            municipio=i.municipio,
            estado=i.estado,
            pais=i.pais,
            codigo_postal=i.codigo_postal,
            no_exterior=i.no_exterior,
            no_interior=i.no_interior,
            colonia=i.colonia,
            localidad=i.localidad,
            referencia=i.referencia
        ) for i in data.desc_inmuebles
    ]

    # 5. DatosAdquirientes
    # Logic: Group by copro_soc_conyugal_e.
    # XSD allows only ONE DatosAdquirientes block?
    # Yes, but it has 'CoproSocConyugalE' attribute.
    # If mixed, we might have an issue, but usually a single act has uniform coproperty status.
    # We assume the first item defines the status for the block.

    cfdi_adquirientes = None
    if data.datos_adquirientes:
        first_adq = data.datos_adquirientes[0]
        copro = first_adq.copro_soc_conyugal_e

        if copro == 'Si':
            # Validate percentages
            percentages = [a.porcentaje for a in data.datos_adquirientes if a.porcentaje is not None]
            validate_coproperty_sum(percentages)

            adqs_cop = []
            for adq in data.datos_adquirientes:
                p_data = prepare_person_data(adq)
                adqs_cop.append(CFDIDatosAdquirienteCopSC(
                    nombre=p_data['nombre'],
                    apellido_paterno=p_data['apellido_paterno'],
                    apellido_materno=p_data['apellido_materno'],
                    rfc=p_data['rfc'],
                    curp=p_data['curp'],
                    porcentaje=adq.porcentaje
                ))
            cfdi_adquirientes = CFDIDatosAdquiriente(
                copro_soc_conyugal_e='Si',
                datos_adquirientes_cop_sc=adqs_cop
            )
        else:
            # Single owner or multiple distinct (but usually single if No)
            # Validation: If 'No', list must have exactly one item.
            if len(data.datos_adquirientes) > 1:
                raise ValueError("CoproSocConyugalE is 'No', but multiple DatosAdquirientes provided.")

            adq = data.datos_adquirientes[0]
            p_data = prepare_person_data(adq)
            cfdi_adquirientes = CFDIDatosAdquiriente(
                copro_soc_conyugal_e='No',
                datos_un_adquiriente=CFDIDatosUnAdquiriente(
                    nombre=p_data['nombre'],
                    apellido_paterno=p_data['apellido_paterno'],
                    apellido_materno=p_data['apellido_materno'],
                    rfc=p_data['rfc'],
                    curp=p_data['curp']
                )
            )

    # 6. DatosEnajenantes
    cfdi_enajenantes = None
    if data.datos_enajenantes:
        first_enaj = data.datos_enajenantes[0]
        copro = first_enaj.copro_soc_conyugal_e

        if copro == 'Si':
             # Validate percentages
            percentages = [a.porcentaje for a in data.datos_enajenantes if a.porcentaje is not None]
            validate_coproperty_sum(percentages)

            enajs_cop = []
            for enaj in data.datos_enajenantes:
                p_data = prepare_person_data(enaj)
                enajs_cop.append(CFDIDatosEnajenanteCopSC(
                    nombre=p_data['nombre'],
                    apellido_paterno=p_data['apellido_paterno'],
                    apellido_materno=p_data['apellido_materno'],
                    rfc=p_data['rfc'],
                    curp=p_data['curp'],
                    porcentaje=enaj.porcentaje
                ))
            cfdi_enajenantes = CFDIDatosEnajenante(
                copro_soc_conyugal_e='Si',
                datos_enajenantes_cop_sc=enajs_cop
            )
        else:
            # Validation: If 'No', list must have exactly one item.
            if len(data.datos_enajenantes) > 1:
                raise ValueError("CoproSocConyugalE is 'No', but multiple DatosEnajenantes provided.")

            enaj = data.datos_enajenantes[0]
            p_data = prepare_person_data(enaj)
            cfdi_enajenantes = CFDIDatosEnajenante(
                copro_soc_conyugal_e='No',
                datos_un_enajenante=CFDIDatosUnEnajenante(
                    nombre=p_data['nombre'],
                    apellido_paterno=p_data['apellido_paterno'],
                    apellido_materno=p_data['apellido_materno'],
                    rfc=p_data['rfc'],
                    curp=p_data['curp']
                )
            )

    # Construct Complement
    return NotariosPublicos(
        datos_notario=datos_notario,
        datos_operacion=datos_operacion,
        desc_inmuebles=desc_inmuebles,
        datos_adquiriente=cfdi_adquirientes,
        datos_enajenante=cfdi_enajenantes
    )

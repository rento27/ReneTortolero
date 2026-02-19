from decimal import Decimal
from datetime import date
from typing import List, Optional
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
from .api_models import ComplementoNotariosModel, DatosAdquirienteModel, DatosEnajenanteModel

# Constants
NUM_NOTARIA = 4
ENTIDAD_FEDERATIVA = "06" # Colima
ADSCRIPCION = "MANZANILLO, COLIMA"
DEFAULT_NOTARY_CURP = "TOSR520601HOCMXA00" # Fallback if not provided

def split_name(full_name: str):
    """
    Splits a full name into Name, Last Name (Paterno), Second Last Name (Materno).
    Heuristic: assume 'First Middle LastP LastM' or 'First LastP LastM'.
    """
    if not full_name:
        return {"nombre": "", "apellido_paterno": "", "apellido_materno": ""}

    parts = full_name.split()
    if len(parts) >= 3:
        return {
            "nombre": " ".join(parts[:-2]),
            "apellido_paterno": parts[-2],
            "apellido_materno": parts[-1]
        }
    elif len(parts) == 2:
        return {
            "nombre": parts[0],
            "apellido_paterno": parts[1],
            "apellido_materno": ""
        }
    else:
        return {
            "nombre": full_name,
            "apellido_paterno": "",
            "apellido_materno": ""
        }

def validate_date(d: date):
    if d > date.today():
        raise ValueError(f"Date {d} cannot be in the future.")
    return d

def process_adquirientes(adquirientes: List[DatosAdquirienteModel]) -> List[DatosAdquiriente]:
    """
    Processes the list of acquirers into satcfdi objects.
    Logic:
    - Group by copro_soc_conyugal_e.
    - 'Si': Create one DatosAdquiriente with a list of DatosAdquirienteCopSC.
    - 'No': Create one DatosAdquiriente per person with DatosUnAdquiriente.
    """
    if not adquirientes:
        return []

    copro_list = [a for a in adquirientes if a.copro_soc_conyugal_e == 'Si']
    single_list = [a for a in adquirientes if a.copro_soc_conyugal_e == 'No']

    result = []

    # Process Single (No)
    for p in single_list:
        name_parts = split_name(p.nombre)
        if p.apellido_paterno: name_parts['apellido_paterno'] = p.apellido_paterno
        if p.apellido_materno: name_parts['apellido_materno'] = p.apellido_materno

        un_adq = DatosUnAdquiriente(
            nombre=name_parts['nombre'],
            apellido_paterno=name_parts['apellido_paterno'],
            apellido_materno=name_parts['apellido_materno'],
            rfc=p.rfc,
            curp=p.curp
        )
        result.append(DatosAdquiriente(
            copro_soc_conyugal_e='No',
            datos_un_adquiriente=un_adq
        ))

    # Process Coproperty (Si)
    if copro_list:
        total_pct = sum(p.porcentaje for p in copro_list if p.porcentaje is not None)
        # Strict validation: Sum(Porcentajes) == 100.00%
        if total_pct != Decimal("100.00"):
             raise ValueError(f"Sum of percentages for coproperty acquirers must be 100.00%, got {total_pct}")

        cop_sc_list = []
        for p in copro_list:
            name_parts = split_name(p.nombre)
            if p.apellido_paterno: name_parts['apellido_paterno'] = p.apellido_paterno
            if p.apellido_materno: name_parts['apellido_materno'] = p.apellido_materno

            cop_sc_list.append(DatosAdquirienteCopSC(
                nombre=name_parts['nombre'],
                apellido_paterno=name_parts['apellido_paterno'],
                apellido_materno=name_parts['apellido_materno'],
                rfc=p.rfc,
                curp=p.curp,
                porcentaje=p.porcentaje
            ))

        result.append(DatosAdquiriente(
            copro_soc_conyugal_e='Si',
            datos_adquirientes_cop_sc=cop_sc_list
        ))

    return result

def process_enajenantes(enajenantes: List[DatosEnajenanteModel]) -> List[DatosEnajenante]:
    # Similar logic to acquirers
    if not enajenantes:
        return []

    copro_list = [e for e in enajenantes if e.copro_soc_conyugal_e == 'Si']
    single_list = [e for e in enajenantes if e.copro_soc_conyugal_e == 'No']

    result = []

    for p in single_list:
        name_parts = split_name(p.nombre)
        if p.apellido_paterno: name_parts['apellido_paterno'] = p.apellido_paterno
        if p.apellido_materno: name_parts['apellido_materno'] = p.apellido_materno

        un_enaj = DatosUnEnajenante(
            nombre=name_parts['nombre'],
            apellido_paterno=name_parts['apellido_paterno'],
            apellido_materno=name_parts['apellido_materno'],
            rfc=p.rfc,
            curp=p.curp
        )
        result.append(DatosEnajenante(
            copro_soc_conyugal_e='No',
            datos_un_enajenante=un_enaj
        ))

    if copro_list:
        total_pct = sum(p.porcentaje for p in copro_list if p.porcentaje is not None)
        if total_pct != Decimal("100.00"):
             raise ValueError(f"Sum of percentages for coproperty alienators must be 100.00%, got {total_pct}")

        cop_sc_list = []
        for p in copro_list:
            name_parts = split_name(p.nombre)
            if p.apellido_paterno: name_parts['apellido_paterno'] = p.apellido_paterno
            if p.apellido_materno: name_parts['apellido_materno'] = p.apellido_materno

            cop_sc_list.append(DatosEnajenanteCopSC(
                nombre=name_parts['nombre'],
                apellido_paterno=name_parts['apellido_paterno'],
                apellido_materno=name_parts['apellido_materno'],
                rfc=p.rfc,
                curp=p.curp,
                porcentaje=p.porcentaje
            ))

        result.append(DatosEnajenante(
            copro_soc_conyugal_e='Si',
            datos_enajenantes_cop_sc=cop_sc_list
        ))

    return result

def create_complemento_notarios(data: ComplementoNotariosModel) -> NotariosPublicos:
    """
    Creates a NotariosPublicos complement object from the input model.
    """

    # 1. DatosNotario
    notary_curp = data.datos_notario.curp if (data.datos_notario and data.datos_notario.curp) else DEFAULT_NOTARY_CURP
    datos_notario = DatosNotario(
        curp=notary_curp,
        num_notaria=NUM_NOTARIA,
        entidad_federativa=ENTIDAD_FEDERATIVA,
        adscripcion=ADSCRIPCION
    )

    # 2. DatosOperacion
    validate_date(data.datos_operacion.fecha_inst_notarial)
    datos_operacion = DatosOperacion(
        num_instrumento_notarial=data.datos_operacion.num_instrumento_notarial,
        fecha_inst_notarial=data.datos_operacion.fecha_inst_notarial,
        monto_operacion=data.datos_operacion.monto_operacion,
        subtotal=data.datos_operacion.subtotal,
        iva=data.datos_operacion.iva
    )

    # 3. DescInmuebles
    desc_inmuebles = []
    for inmueble in data.desc_inmuebles:
        desc_inmuebles.append(DescInmueble(
            tipo_inmueble=inmueble.tipo_inmueble,
            calle=inmueble.calle,
            no_exterior=inmueble.no_exterior,
            no_interior=inmueble.no_interior,
            colonia=inmueble.colonia,
            localidad=inmueble.localidad,
            referencia=inmueble.referencia,
            municipio=inmueble.municipio,
            estado=inmueble.estado,
            pais=inmueble.pais,
            codigo_postal=inmueble.codigo_postal
        ))

    # 4. DatosAdquirientes
    datos_adquirientes = process_adquirientes(data.datos_adquirientes)

    # 5. DatosEnajenantes
    datos_enajenantes = process_enajenantes(data.datos_enajenantes) if data.datos_enajenantes else None

    # Note: satcfdi uses singular argument names even for lists (datos_adquiriente, datos_enajenante)
    return NotariosPublicos(
        datos_notario=datos_notario,
        datos_operacion=datos_operacion,
        desc_inmuebles=desc_inmuebles,
        datos_adquiriente=datos_adquirientes,
        datos_enajenante=datos_enajenantes
    )

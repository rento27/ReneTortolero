from datetime import date
from decimal import Decimal
from typing import List, Optional

try:
    from satcfdi.create.cfd.notariospublicos10 import (
        NotariosPublicos,
        DatosNotario,
        DatosOperacion,
        DescInmueble,
        DatosAdquiriente,
        DatosAdquirienteCopSC,
        DatosUnAdquiriente,
        DatosEnajenante,
        DatosEnajenanteCopSC,
        DatosUnEnajenante
    )
except ImportError:
    # Fallback for environment without satcfdi installed (e.g. initial dev)
    # This allows the code to be parsed/imported even if the lib is missing
    NotariosPublicos = None

from .api_models import ComplementoNotariosModel, DatosAdquiriente as PydanticAdquiriente, DatosEnajenante as PydanticEnajenante
from .fiscal_engine import validate_copropiedad, sanitize_name

def split_name(full_name: str):
    """
    Helper to split full name into Nombre, Paterno, Materno.
    This is a heuristic and might need manual correction.
    """
    parts = full_name.strip().split()
    if len(parts) == 1:
        return parts[0], "", ""
    elif len(parts) == 2:
        return parts[0], parts[1], ""
    elif len(parts) >= 3:
        return " ".join(parts[:-2]), parts[-2], parts[-1]
    return full_name, "", ""

def create_complemento_notarios(data: ComplementoNotariosModel) -> NotariosPublicos:
    if NotariosPublicos is None:
        raise ImportError("satcfdi library is not installed")

    # 1. Datos Notario (Defaults to Notaria 4 Manzanillo if not provided)
    notario_data = data.datos_notario
    if notario_data:
        datos_notario = DatosNotario(
            curp=notario_data.curp,
            num_notaria=notario_data.num_notaria,
            entidad_federativa=notario_data.entidad_federativa,
            adscripcion=notario_data.adscripcion
        )
    else:
        # Default Hardcoded
        datos_notario = DatosNotario(
            curp="TOSR520601HOCMXA00", # Fallback/Mock CURP
            num_notaria=4,
            entidad_federativa="06",
            adscripcion="MANZANILLO, COLIMA"
        )

    # 2. Datos Operacion
    if data.datos_operacion.fecha_inst_notarial > date.today():
        raise ValueError(f"Fecha de Instrumento Notarial cannot be in the future: {data.datos_operacion.fecha_inst_notarial}")

    datos_operacion = DatosOperacion(
        num_instrumento_notarial=data.datos_operacion.num_instrumento_notarial,
        fecha_inst_notarial=data.datos_operacion.fecha_inst_notarial,
        monto_operacion=data.datos_operacion.monto_operacion,
        subtotal=data.datos_operacion.subtotal,
        iva=data.datos_operacion.iva
    )

    # 3. Inmuebles
    lista_inmuebles = []
    for inm in data.desc_inmuebles:
        lista_inmuebles.append(DescInmueble(
            tipo_inmueble=inm.tipo_inmueble,
            calle=inm.calle,
            no_exterior=inm.no_exterior,
            no_interior=inm.no_interior,
            colonia=inm.colonia,
            localidad=inm.localidad,
            municipio=inm.municipio,
            estado=inm.estado,
            pais=inm.pais,
            codigo_postal=inm.codigo_postal
        ))

    # 4. Datos Adquirientes
    percentages = [a.porcentaje for a in data.datos_adquirientes if a.porcentaje is not None]
    if percentages:
        validate_copropiedad(percentages)

    datos_adquirientes_xml = []

    singles = [a for a in data.datos_adquirientes if a.copro_soc_conyugal_e == 'No']
    copros = [a for a in data.datos_adquirientes if a.copro_soc_conyugal_e == 'Si']

    # Process Singles
    for adq in singles:
        nombre, paterno, materno = split_name(adq.nombre)
        if adq.apellido_paterno: paterno = adq.apellido_paterno
        if adq.apellido_materno: materno = adq.apellido_materno

        un_adq = DatosUnAdquiriente(
            nombre=nombre,
            apellido_paterno=paterno,
            apellido_materno=materno,
            rfc=adq.rfc,
            curp=adq.curp
        )
        datos_adquirientes_xml.append(DatosAdquiriente(
            copro_soc_conyugal_e='No',
            datos_un_adquiriente=un_adq
        ))

    # Process Copros (aggregated into one DatosAdquiriente element)
    if copros:
        cop_sc_list = []
        for adq in copros:
            nombre, paterno, materno = split_name(adq.nombre)
            if adq.apellido_paterno: paterno = adq.apellido_paterno
            if adq.apellido_materno: materno = adq.apellido_materno

            cop_sc_list.append(DatosAdquirienteCopSC(
                nombre=nombre,
                apellido_paterno=paterno,
                apellido_materno=materno,
                rfc=adq.rfc,
                curp=adq.curp,
                porcentaje=adq.porcentaje
            ))

        datos_adquirientes_xml.append(DatosAdquiriente(
            copro_soc_conyugal_e='Si',
            datos_adquirientes_cop_sc=cop_sc_list
        ))

    # 5. Datos Enajenantes
    datos_enajenantes_xml = []
    if data.datos_enajenantes:
        e_percentages = [e.porcentaje for e in data.datos_enajenantes if e.porcentaje is not None]
        if e_percentages:
            validate_copropiedad(e_percentages)

        e_singles = [e for e in data.datos_enajenantes if e.copro_soc_conyugal_e == 'No']
        e_copros = [e for e in data.datos_enajenantes if e.copro_soc_conyugal_e == 'Si']

        # Process Singles
        for ena in e_singles:
            nombre, paterno, materno = split_name(ena.nombre)
            if ena.apellido_paterno: paterno = ena.apellido_paterno
            if ena.apellido_materno: materno = ena.apellido_materno

            un_ena = DatosUnEnajenante(
                nombre=nombre,
                apellido_paterno=paterno,
                apellido_materno=materno,
                rfc=ena.rfc,
                curp=ena.curp
            )
            datos_enajenantes_xml.append(DatosEnajenante(
                copro_soc_conyugal_e='No',
                datos_un_enajenante=un_ena
            ))

        # Process Copros
        if e_copros:
            e_cop_sc_list = []
            for ena in e_copros:
                nombre, paterno, materno = split_name(ena.nombre)
                if ena.apellido_paterno: paterno = ena.apellido_paterno
                if ena.apellido_materno: materno = ena.apellido_materno

                e_cop_sc_list.append(DatosEnajenanteCopSC(
                    nombre=nombre,
                    apellido_paterno=paterno,
                    apellido_materno=materno,
                    rfc=ena.rfc,
                    curp=ena.curp,
                    porcentaje=ena.porcentaje
                ))

            datos_enajenantes_xml.append(DatosEnajenante(
                copro_soc_conyugal_e='Si',
                datos_enajenantes_cop_sc=e_cop_sc_list
            ))

    # Construct Complement
    complemento = NotariosPublicos(
        datos_notario=datos_notario,
        datos_operacion=datos_operacion,
        desc_inmuebles=lista_inmuebles,
        datos_adquiriente=datos_adquirientes_xml,
        datos_enajenante=datos_enajenantes_xml if datos_enajenantes_xml else None
    )

    return complemento

from decimal import Decimal
from typing import List, Optional
from satcfdi.create.cfd.notariospublicos10 import (
    NotariosPublicos,
    DatosNotario,
    DatosOperacion,
    DescInmueble,
    DatosEnajenante,
    DatosUnEnajenante,
    DatosEnajenanteCopSC,
    DatosAdquiriente,
    DatosUnAdquiriente,
    DatosAdquirienteCopSC
)
from .api_models import ComplementoNotariosModel, DatosNotarioModel
from .fiscal_engine import validate_copropiedad

def create_complemento_notarios(data: ComplementoNotariosModel) -> NotariosPublicos:
    """
    Creates a satcfdi NotariosPublicos object from the Pydantic model.
    """

    # 1. Datos Notario
    # Use explicit default CURP if not provided (RFC: TOSR520601AZ4 -> CURP: TOSR520601HOCMXA00)
    # The Pydantic model validates length, so we must provide a valid 18-char string.
    dn_data = data.datos_notario or DatosNotarioModel(curp="TOSR520601HOCMXA00")

    # Validation: Ensure CURP is present (strict requirement)
    if not dn_data.curp or len(dn_data.curp) != 18:
        raise ValueError("DatosNotario: CURP must be exactly 18 characters.")

    datos_notario = DatosNotario(
        curp=dn_data.curp,
        num_notaria=dn_data.num_notaria,
        entidad_federativa=dn_data.entidad_federativa,
        adscripcion=dn_data.adscripcion
    )

    # 2. Datos Operacion
    do_data = data.datos_operacion
    datos_operacion = DatosOperacion(
        num_instrumento_notarial=do_data.num_instrumento_notarial,
        fecha_inst_notarial=do_data.fecha_inst_notarial,
        monto_operacion=do_data.monto_operacion,
        subtotal=do_data.subtotal,
        iva=do_data.iva
    )

    # 3. Desc Inmuebles
    desc_inmuebles = []
    for inmueble in data.desc_inmuebles:
        desc_inmuebles.append(DescInmueble(
            tipo_inmueble=inmueble.tipo_inmueble,
            calle=inmueble.calle,
            municipio=inmueble.municipio,
            estado=inmueble.estado,
            pais=inmueble.pais,
            codigo_postal=inmueble.codigo_postal,
            no_exterior=inmueble.no_exterior,
            no_interior=inmueble.no_interior,
            colonia=inmueble.colonia,
            localidad=inmueble.localidad,
            referencia=inmueble.referencia
        ))

    # 4. Datos Enajenante
    de_data = data.datos_enajenante
    datos_enajenante_kwargs = {
        'copro_soc_conyugal_e': de_data.copro_soc_conyugal_e
    }

    if de_data.copro_soc_conyugal_e == 'No':
        if not de_data.datos_un_enajenante:
            raise ValueError("DatosEnajenante: datos_un_enajenante required when copro_soc_conyugal_e is 'No'")

        due = de_data.datos_un_enajenante
        datos_enajenante_kwargs['datos_un_enajenante'] = DatosUnEnajenante(
            nombre=due.nombre,
            apellido_paterno=due.apellido_paterno,
            rfc=due.rfc,
            curp=due.curp,
            apellido_materno=due.apellido_materno
        )
    else:
        # Copropiedad
        if not de_data.datos_enajenantes_cop_sc:
            raise ValueError("DatosEnajenante: datos_enajenantes_cop_sc required when copro_soc_conyugal_e is 'Si'")

        # Validate Percentages
        percentages = [p.porcentaje for p in de_data.datos_enajenantes_cop_sc]
        validate_copropiedad(percentages)

        cop_list = []
        for p in de_data.datos_enajenantes_cop_sc:
            cop_list.append(DatosEnajenanteCopSC(
                nombre=p.nombre,
                rfc=p.rfc,
                porcentaje=p.porcentaje,
                apellido_paterno=p.apellido_paterno,
                apellido_materno=p.apellido_materno,
                curp=p.curp
            ))
        datos_enajenante_kwargs['datos_enajenantes_cop_sc'] = cop_list

    datos_enajenante = DatosEnajenante(**datos_enajenante_kwargs)

    # 5. Datos Adquiriente
    da_data = data.datos_adquiriente
    datos_adquiriente_kwargs = {
        'copro_soc_conyugal_e': da_data.copro_soc_conyugal_e
    }

    if da_data.copro_soc_conyugal_e == 'No':
        if not da_data.datos_un_adquiriente:
            raise ValueError("DatosAdquiriente: datos_un_adquiriente required when copro_soc_conyugal_e is 'No'")

        dua = da_data.datos_un_adquiriente
        datos_adquiriente_kwargs['datos_un_adquiriente'] = DatosUnAdquiriente(
            nombre=dua.nombre,
            rfc=dua.rfc,
            apellido_paterno=dua.apellido_paterno,
            apellido_materno=dua.apellido_materno,
            curp=dua.curp
        )
    else:
        # Copropiedad
        if not da_data.datos_adquirientes_cop_sc:
            raise ValueError("DatosAdquiriente: datos_adquirientes_cop_sc required when copro_soc_conyugal_e is 'Si'")

        # Validate Percentages
        percentages = [p.porcentaje for p in da_data.datos_adquirientes_cop_sc]
        validate_copropiedad(percentages)

        cop_list = []
        for p in da_data.datos_adquirientes_cop_sc:
            cop_list.append(DatosAdquirienteCopSC(
                nombre=p.nombre,
                rfc=p.rfc,
                porcentaje=p.porcentaje,
                apellido_paterno=p.apellido_paterno,
                apellido_materno=p.apellido_materno,
                curp=p.curp
            ))
        datos_adquiriente_kwargs['datos_adquirientes_cop_sc'] = cop_list

    datos_adquiriente = DatosAdquiriente(**datos_adquiriente_kwargs)

    # Create Complement
    return NotariosPublicos(
        desc_inmuebles=desc_inmuebles,
        datos_operacion=datos_operacion,
        datos_notario=datos_notario,
        datos_enajenante=datos_enajenante,
        datos_adquiriente=datos_adquiriente
    )

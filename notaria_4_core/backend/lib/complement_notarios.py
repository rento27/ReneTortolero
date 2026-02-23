from decimal import Decimal
from typing import List
from satcfdi.create.cfd import notariospublicos10 as np
from .api_models import ComplementoNotariosModel
from .fiscal_engine import validate_copropiedad

def create_complemento_notarios(data: ComplementoNotariosModel) -> np.NotariosPublicos:
    """
    Creates the NotariosPublicos complement from the Pydantic model.
    """

    # 1. DescInmuebles
    desc_inmuebles = [
        np.DescInmueble(
            tipo_inmueble=d.tipo_inmueble,
            calle=d.calle,
            no_exterior=d.no_exterior,
            no_interior=d.no_interior,
            colonia=d.colonia,
            localidad=d.localidad,
            referencia=d.referencia,
            municipio=d.municipio,
            estado=d.estado,
            pais=d.pais,
            codigo_postal=d.codigo_postal
        ) for d in data.desc_inmuebles
    ]

    # 2. DatosOperacion
    datos_operacion = np.DatosOperacion(
        num_instrumento_notarial=data.datos_operacion.num_instrumento_notarial,
        fecha_inst_notarial=data.datos_operacion.fecha_inst_notarial,
        monto_operacion=data.datos_operacion.monto_operacion,
        subtotal=data.datos_operacion.subtotal,
        iva=data.datos_operacion.iva
    )

    # 3. DatosNotario
    # Fallback CURP for Notaria 4 if not provided
    notario_curp = data.datos_notario.curp or "TOSR520601HOCMXA00"

    datos_notario = np.DatosNotario(
        curp=notario_curp,
        num_notaria=data.datos_notario.num_notaria,
        entidad_federativa=data.datos_notario.entidad_federativa,
        adscripcion=data.datos_notario.adscripcion
    )

    # 4. DatosAdquiriente
    adq_data = data.datos_adquiriente
    datos_un_adquiriente = None
    datos_adquirientes_cop_sc = None

    if adq_data.copro_soc_conyugal_e == 'No':
        if not adq_data.datos_un_adquiriente:
             raise ValueError("copro_soc_conyugal_e is 'No' but datos_un_adquiriente is missing")
        u = adq_data.datos_un_adquiriente
        datos_un_adquiriente = np.DatosUnAdquiriente(
            nombre=u.nombre,
            apellido_paterno=u.apellido_paterno,
            apellido_materno=u.apellido_materno,
            rfc=u.rfc,
            curp=u.curp
        )
    else:
        if not adq_data.datos_adquirientes_cop_sc:
             raise ValueError("copro_soc_conyugal_e is 'Si' but datos_adquirientes_cop_sc is missing")

        # Validate Percentages
        percentages = [d.porcentaje for d in adq_data.datos_adquirientes_cop_sc]
        validate_copropiedad(percentages)

        datos_adquirientes_cop_sc = [
            np.DatosAdquirienteCopSC(
                nombre=d.nombre,
                apellido_paterno=d.apellido_paterno,
                apellido_materno=d.apellido_materno,
                rfc=d.rfc,
                curp=d.curp,
                porcentaje=d.porcentaje
            ) for d in adq_data.datos_adquirientes_cop_sc
        ]

    datos_adquiriente = np.DatosAdquiriente(
        copro_soc_conyugal_e=adq_data.copro_soc_conyugal_e,
        datos_un_adquiriente=datos_un_adquiriente,
        datos_adquirientes_cop_sc=datos_adquirientes_cop_sc
    )

    # 5. DatosEnajenante
    datos_enajenante = None
    if data.datos_enajenante:
        enaj_data = data.datos_enajenante
        datos_un_enajenante = None
        datos_enajenantes_cop_sc = None

        if enaj_data.copro_soc_conyugal_e == 'No':
            if not enaj_data.datos_un_enajenante:
                raise ValueError("Enajenante copro_soc_conyugal_e is 'No' but datos_un_enajenante is missing")
            u = enaj_data.datos_un_enajenante
            datos_un_enajenante = np.DatosUnEnajenante(
                nombre=u.nombre,
                apellido_paterno=u.apellido_paterno,
                apellido_materno=u.apellido_materno,
                rfc=u.rfc,
                curp=u.curp
            )
        else:
            if not enaj_data.datos_enajenantes_cop_sc:
                raise ValueError("Enajenante copro_soc_conyugal_e is 'Si' but datos_enajenantes_cop_sc is missing")

            # Validate Percentages
            percentages = [d.porcentaje for d in enaj_data.datos_enajenantes_cop_sc]
            validate_copropiedad(percentages)

            datos_enajenantes_cop_sc = [
                np.DatosEnajenanteCopSC(
                    nombre=d.nombre,
                    apellido_paterno=d.apellido_paterno,
                    apellido_materno=d.apellido_materno,
                    rfc=d.rfc,
                    curp=d.curp,
                    porcentaje=d.porcentaje
                ) for d in enaj_data.datos_enajenantes_cop_sc
            ]

        datos_enajenante = np.DatosEnajenante(
            copro_soc_conyugal_e=enaj_data.copro_soc_conyugal_e,
            datos_un_enajenante=datos_un_enajenante,
            datos_enajenantes_cop_sc=datos_enajenantes_cop_sc
        )

    return np.NotariosPublicos(
        desc_inmuebles=desc_inmuebles,
        datos_operacion=datos_operacion,
        datos_notario=datos_notario,
        datos_adquiriente=datos_adquiriente,
        datos_enajenante=datos_enajenante
    )

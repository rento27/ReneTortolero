from decimal import Decimal
from datetime import date
from typing import List
from .api_models import ComplementoNotariosModel

# Import satcfdi classes
try:
    from satcfdi.create.cfd.notariospublicos10 import (
        NotariosPublicos,
        DatosNotario,
        DatosOperacion,
        DescInmueble,
        DatosAdquiriente,
        DatosEnajenante,
        DatosUnAdquiriente,
        DatosAdquirienteCopSC,
        DatosUnEnajenante,
        DatosEnajenanteCopSC
    )
except ImportError:
    # Handle environment where satcfdi is not installed (e.g., during some tests or builds)
    # But usually it should be installed.
    NotariosPublicos = None

# Constants for Notaria 4
NUM_NOTARIA = 4
ENTIDAD_FEDERATIVA = "06"
ADSCRIPCION = "MANZANILLO, COLIMA"
FALLBACK_CURP_NOTARY = "TOSR520601HOCMXA00" # Rene Manuel Tortolero Santillana

def validate_percentage_sum(items: list, context: str):
    """
    Validates that the sum of percentages in the list is exactly 100.00.
    """
    if not items:
        return

    total = sum(item.porcentaje for item in items)
    if total != Decimal("100.00"):
        raise ValueError(f"Sum of percentages for {context} must be 100.00%, got {total}")

def create_complemento_notarios(data: ComplementoNotariosModel):
    if NotariosPublicos is None:
        raise ImportError("satcfdi library is not available")

    # 1. Validate Dates
    if data.datos_operacion.fecha_inst_notarial > date.today():
         raise ValueError("FechaInstNotarial cannot be in the future")

    # 2. Datos Notario (Apply defaults)
    notario_curp = data.datos_notario.curp if data.datos_notario and data.datos_notario.curp else FALLBACK_CURP_NOTARY

    datos_notario = DatosNotario(
        curp=notario_curp,
        num_notaria=NUM_NOTARIA,
        entidad_federativa=ENTIDAD_FEDERATIVA,
        adscripcion=ADSCRIPCION
    )

    # 3. Datos Operacion
    # Note: satcfdi uses 'subtotal' (lowercase) or 'sub_total'? Memory said 'subtotal'.
    datos_operacion = DatosOperacion(
        num_instrumento_notarial=data.datos_operacion.num_instrumento_notarial,
        fecha_inst_notarial=data.datos_operacion.fecha_inst_notarial,
        monto_operacion=data.datos_operacion.monto_operacion,
        subtotal=data.datos_operacion.subtotal,
        iva=data.datos_operacion.iva
    )

    # 4. DescInmuebles (List of DescInmueble)
    desc_inmuebles = [
        DescInmueble(
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

    # 5. Datos Adquiriente
    adquiriente_kwargs = {
        "copro_soc_conyugal_e": data.datos_adquiriente.copro_soc_conyugal_e
    }

    if data.datos_adquiriente.copro_soc_conyugal_e == "No":
        if not data.datos_adquiriente.datos_un_adquiriente:
             raise ValueError("datos_un_adquiriente required when copro_soc_conyugal_e is 'No'")
        ua = data.datos_adquiriente.datos_un_adquiriente
        adquiriente_kwargs["datos_un_adquiriente"] = DatosUnAdquiriente(
            nombre=ua.nombre,
            apellido_paterno=ua.apellido_paterno,
            apellido_materno=ua.apellido_materno,
            rfc=ua.rfc,
            curp=ua.curp
        )
    else:
        if not data.datos_adquiriente.datos_adquirientes_cop_sc:
             raise ValueError("datos_adquirientes_cop_sc required when copro_soc_conyugal_e is 'Si'")

        # Validate Percentage Sum
        validate_percentage_sum(data.datos_adquiriente.datos_adquirientes_cop_sc, "Adquirientes")

        adquiriente_kwargs["datos_adquirientes_cop_sc"] = [
            DatosAdquirienteCopSC(
                nombre=ac.nombre,
                apellido_paterno=ac.apellido_paterno,
                apellido_materno=ac.apellido_materno,
                rfc=ac.rfc,
                curp=ac.curp,
                porcentaje=ac.porcentaje
            ) for ac in data.datos_adquiriente.datos_adquirientes_cop_sc
        ]

    datos_adquiriente = DatosAdquiriente(**adquiriente_kwargs)

    # 6. Datos Enajenante (Optional)
    datos_enajenante = None
    if data.datos_enajenante:
        enajenante_kwargs = {
            "copro_soc_conyugal_e": data.datos_enajenante.copro_soc_conyugal_e
        }
        if data.datos_enajenante.copro_soc_conyugal_e == "No":
             if not data.datos_enajenante.datos_un_enajenante:
                 raise ValueError("datos_un_enajenante required when copro_soc_conyugal_e is 'No'")
             ue = data.datos_enajenante.datos_un_enajenante
             enajenante_kwargs["datos_un_enajenante"] = DatosUnEnajenante(
                 nombre=ue.nombre,
                 apellido_paterno=ue.apellido_paterno,
                 apellido_materno=ue.apellido_materno,
                 rfc=ue.rfc,
                 curp=ue.curp
             )
        else:
            if not data.datos_enajenante.datos_enajenante_cop_sc:
                raise ValueError("datos_enajenante_cop_sc required when copro_soc_conyugal_e is 'Si'")

            # Validate Percentage Sum
            validate_percentage_sum(data.datos_enajenante.datos_enajenante_cop_sc, "Enajenantes")

            enajenante_kwargs["datos_enajenantes_cop_sc"] = [
                DatosEnajenanteCopSC(
                    nombre=ec.nombre,
                    apellido_paterno=ec.apellido_paterno,
                    apellido_materno=ec.apellido_materno,
                    rfc=ec.rfc,
                    curp=ec.curp,
                    porcentaje=ec.porcentaje
                ) for ec in data.datos_enajenante.datos_enajenante_cop_sc
            ]

        datos_enajenante = DatosEnajenante(**enajenante_kwargs)

    # Construct the Complement
    return NotariosPublicos(
        datos_notario=datos_notario,
        datos_operacion=datos_operacion,
        desc_inmuebles=desc_inmuebles,
        datos_adquiriente=datos_adquiriente,
        datos_enajenante=datos_enajenante
    )

from datetime import date
from decimal import Decimal
from typing import List, Tuple
from satcfdi.create.cfd.notariospublicos10 import (
    NotariosPublicos, DatosNotario, DatosOperacion, DescInmueble,
    DatosAdquiriente, DatosAdquirienteCopSC, DatosEnajenante, DatosEnajenanteCopSC,
    DatosUnAdquiriente, DatosUnEnajenante
)
from .api_models import ComplementoNotariosModel
from .fiscal_engine import validate_copropiedad, sanitize_name

# Fallback CURP for Notary if not provided
FALLBACK_NOTARY_CURP = "TOSR520601HOCMXA00"

def split_name(full_name: str) -> Tuple[str, str, str]:
    """
    Splits a full name into Name, Paternal Surname, Maternal Surname.
    This is a naive implementation as a fallback.
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
    """
    Creates a NotariosPublicos complement object from the Pydantic model.
    """

    # 1. Validate Notary Data
    notary_curp = data.datos_notario.curp or FALLBACK_NOTARY_CURP

    datos_notario = DatosNotario(
        num_notaria=data.datos_notario.num_notaria,
        curp=notary_curp,
        entidad_federativa=data.datos_notario.entidad_federativa,
        adscripcion=data.datos_notario.adscripcion
    )

    # 2. Validate Operation Data
    if data.datos_operacion.fecha_inst_notarial > date.today():
        raise ValueError(f"FechaInstNotarial cannot be in the future: {data.datos_operacion.fecha_inst_notarial}")

    datos_operacion = DatosOperacion(
        num_instrumento_notarial=data.datos_operacion.num_instrumento_notarial,
        fecha_inst_notarial=data.datos_operacion.fecha_inst_notarial,
        monto_operacion=data.datos_operacion.monto_operacion,
        subtotal=data.datos_operacion.subtotal,
        iva=data.datos_operacion.iva
    )

    # 3. Process Inmueble
    desc_inmuebles = DescInmueble(
        tipo_inmueble=data.datos_inmueble.tipo_inmueble,
        calle=data.datos_inmueble.calle,
        no_exterior=data.datos_inmueble.no_exterior,
        no_interior=data.datos_inmueble.no_interior,
        colonia=data.datos_inmueble.colonia,
        localidad=data.datos_inmueble.localidad,
        referencia=data.datos_inmueble.referencia,
        municipio=data.datos_inmueble.municipio,
        estado=data.datos_inmueble.estado,
        pais=data.datos_inmueble.pais,
        codigo_postal=data.datos_inmueble.codigo_postal
    )

    # 4. Process Adquirientes (Acquirers)
    percentages = [d.porcentaje for d in data.datos_adquirientes]
    validate_copropiedad(percentages)

    list_datos_adquiriente_objects = []

    if data.datos_adquirientes:
        is_copro = len(data.datos_adquirientes) > 1 or data.datos_adquirientes[0].copro_soc_conyugal_e == 'Si'

        if is_copro:
            # Create ONE DatosAdquiriente group with CoproSocConyugalE='Si'
            main_adq = data.datos_adquirientes[0]
            mn, mp, mm = main_adq.nombre, main_adq.apellido_paterno, main_adq.apellido_materno
            if not mp and not mm:
                mn, mp, mm = split_name(main_adq.nombre)

            # Main person details in DatosUnAdquiriente
            datos_un_adq = DatosUnAdquiriente(
                nombre=mn,
                apellido_paterno=mp or ".", # Fallback dot if empty
                apellido_materno=mm,
                rfc=main_adq.rfc,
                curp=main_adq.curp
            )

            # List of coproprietors (ALL persons) in DatosAdquirienteCopSC
            cop_sc_list = []
            for adq in data.datos_adquirientes:
                n, p, m = adq.nombre, adq.apellido_paterno, adq.apellido_materno
                if not p and not m:
                    n, p, m = split_name(adq.nombre)

                cop_sc_list.append(DatosAdquirienteCopSC(
                    nombre=n,
                    apellido_paterno=p or ".",
                    apellido_materno=m,
                    rfc=adq.rfc,
                    curp=adq.curp,
                    porcentaje=adq.porcentaje
                ))

            list_datos_adquiriente_objects.append(DatosAdquiriente(
                copro_soc_conyugal_e='Si',
                datos_un_adquiriente=datos_un_adq,
                datos_adquirientes_cop_sc=cop_sc_list
            ))

        else:
            # Single person, CoproSocConyugalE='No'
            adq = data.datos_adquirientes[0]
            n, p, m = adq.nombre, adq.apellido_paterno, adq.apellido_materno
            if not p and not m:
                n, p, m = split_name(adq.nombre)

            datos_un_adq = DatosUnAdquiriente(
                nombre=n,
                apellido_paterno=p or ".",
                apellido_materno=m,
                rfc=adq.rfc,
                curp=adq.curp
            )

            list_datos_adquiriente_objects.append(DatosAdquiriente(
                copro_soc_conyugal_e='No',
                datos_un_adquiriente=datos_un_adq
            ))

    # 5. Process Enajenantes (Alienators)
    percentages_enaj = [d.porcentaje for d in data.datos_enajenantes]
    validate_copropiedad(percentages_enaj)

    list_datos_enajenante_objects = []

    if data.datos_enajenantes:
        is_copro_enaj = len(data.datos_enajenantes) > 1 or data.datos_enajenantes[0].copro_soc_conyugal_e == 'Si'

        if is_copro_enaj:
            main_enaj = data.datos_enajenantes[0]
            mn, mp, mm = main_enaj.nombre, main_enaj.apellido_paterno, main_enaj.apellido_materno
            if not mp and not mm:
                mn, mp, mm = split_name(main_enaj.nombre)

            datos_un_enaj = DatosUnEnajenante(
                nombre=mn,
                apellido_paterno=mp or ".",
                apellido_materno=mm,
                rfc=main_enaj.rfc,
                curp=main_enaj.curp # Mandatory
            )

            cop_sc_list_enaj = []
            for enaj in data.datos_enajenantes:
                n, p, m = enaj.nombre, enaj.apellido_paterno, enaj.apellido_materno
                if not p and not m:
                    n, p, m = split_name(enaj.nombre)

                cop_sc_list_enaj.append(DatosEnajenanteCopSC(
                    nombre=n,
                    apellido_paterno=p or ".",
                    apellido_materno=m,
                    rfc=enaj.rfc,
                    curp=enaj.curp,
                    porcentaje=enaj.porcentaje
                ))

            list_datos_enajenante_objects.append(DatosEnajenante(
                copro_soc_conyugal_e='Si',
                datos_un_enajenante=datos_un_enaj,
                datos_enajenantes_cop_sc=cop_sc_list_enaj
            ))
        else:
            enaj = data.datos_enajenantes[0]
            n, p, m = enaj.nombre, enaj.apellido_paterno, enaj.apellido_materno
            if not p and not m:
                n, p, m = split_name(enaj.nombre)

            datos_un_enaj = DatosUnEnajenante(
                nombre=n,
                apellido_paterno=p or ".",
                apellido_materno=m,
                rfc=enaj.rfc,
                curp=enaj.curp
            )

            list_datos_enajenante_objects.append(DatosEnajenante(
                copro_soc_conyugal_e='No',
                datos_un_enajenante=datos_un_enaj
            ))

    # 6. Build Complement
    # satcfdi v4 NotariosPublicos expects singular objects for datos_adquiriente/datos_enajenante
    # We extract the single object created above.
    # Note: Our logic guarantees only one object is created (either copro group or single).

    adquiriente_obj = list_datos_adquiriente_objects[0] if list_datos_adquiriente_objects else None
    enajenante_obj = list_datos_enajenante_objects[0] if list_datos_enajenante_objects else None

    return NotariosPublicos(
        datos_notario=datos_notario,
        datos_operacion=datos_operacion,
        desc_inmuebles=[desc_inmuebles],
        datos_adquiriente=adquiriente_obj,
        datos_enajenante=enajenante_obj
    )

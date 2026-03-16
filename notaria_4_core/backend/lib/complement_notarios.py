import re
import datetime
from decimal import Decimal
from typing import List, Dict, Any

from satcfdi.create.cfd import notariospublicos10

from .fiscal_engine import sanitize_name

def split_name(full_name: str, apellido_paterno: str = "", apellido_materno: str = "") -> tuple[str, str, str]:
    if apellido_paterno or apellido_materno:
        return full_name, apellido_paterno, apellido_materno

    parts = full_name.strip().split()
    if len(parts) == 1:
        return full_name, "", ""
    elif len(parts) == 2:
        return parts[0], parts[1], ""
    elif len(parts) >= 3:
        # Simplistic heuristic: first word is name, last two are surnames
        nombre = " ".join(parts[:-2])
        ap = parts[-2]
        am = parts[-1]
        return nombre, ap, am
    return full_name, "", ""

def create_complemento_notarios(data: Any) -> Any: # Receives ComplementoNotariosModel
    # 1. Validation
    inst_date = datetime.datetime.strptime(data.datos_operacion.fecha_inst_notarial, "%Y-%m-%d").date()
    if inst_date > datetime.date.today():
        raise ValueError("FechaInstNotarial cannot be in the future.")

    sum_adq = sum([adq.porcentaje for adq in data.datos_adquiriente if adq.porcentaje is not None])
    if sum_adq > 0 and sum_adq != Decimal("100.00"):
        raise ValueError("Sum of percentages for Adquirientes must be exactly 100.00 if provided.")

    sum_enaj = sum([enaj.porcentaje for enaj in data.datos_enajenante if enaj.porcentaje is not None])
    if sum_enaj > 0 and sum_enaj != Decimal("100.00"):
        raise ValueError("Sum of percentages for Enajenantes must be exactly 100.00 if provided.")

    # 2. Build DatosNotario
    dn = data.datos_notario
    datos_notario = notariospublicos10.DatosNotario(
        curp=dn.curp,
        num_notaria=dn.num_notaria,
        entidad_federativa=dn.entidad_federativa,
        adscripcion=dn.adscripcion
    )

    # 3. Build DatosOperacion
    do = data.datos_operacion
    datos_operacion = notariospublicos10.DatosOperacion(
        num_instrumento_notarial=do.num_instrumento_notarial,
        fecha_inst_notarial=do.fecha_inst_notarial,
        monto_operacion=do.monto_operacion,
        subtotal=do.subtotal,
        iva=do.iva
    )

    # 4. Build DescInmuebles
    desc_inmuebles = []
    for di in data.desc_inmuebles:
        desc_inmuebles.append(notariospublicos10.DescInmueble(
            tipo_inmueble=di.tipo_inmueble,
            calle=di.calle,
            municipio=di.municipio,
            estado=di.estado,
            pais=di.pais,
            codigo_postal=di.codigo_postal,
            no_exterior=di.no_exterior,
            no_interior=di.no_interior,
            colonia=di.colonia,
            localidad=di.localidad,
            referencia=di.referencia
        ))

    # 5. Build Adquirientes
    adquirientes_cop = []
    adquiriente_unico = None
    if len(data.datos_adquiriente) == 1 and data.datos_adquiriente[0].copro_soc_conyugal_e == "No":
        adq = data.datos_adquiriente[0]
        n, ap, am = split_name(sanitize_name(adq.nombre), adq.apellido_paterno, adq.apellido_materno)
        adquiriente_unico = notariospublicos10.DatosUnAdquiriente(
            nombre=n,
            apellido_paterno=ap,
            apellido_materno=am,
            rfc=adq.rfc,
            curp=adq.curp
        )
        datos_adquiriente = notariospublicos10.DatosAdquiriente(
            copro_soc_conyugal_e="No",
            datos_un_adquiriente=adquiriente_unico
        )
    else:
        for adq in data.datos_adquiriente:
            if adq.copro_soc_conyugal_e == "No":
                raise ValueError("CoproSocConyugalE is 'No' but multiple Adquirientes found.")
            n, ap, am = split_name(sanitize_name(adq.nombre), adq.apellido_paterno, adq.apellido_materno)
            adquirientes_cop.append(notariospublicos10.DatosAdquirienteCopSC(
                nombre=n,
                apellido_paterno=ap,
                apellido_materno=am,
                rfc=adq.rfc,
                curp=adq.curp,
                porcentaje=adq.porcentaje
            ))
        datos_adquiriente = notariospublicos10.DatosAdquiriente(
            copro_soc_conyugal_e="Si",
            datos_adquirientes_cop_sc=adquirientes_cop
        )

    # 6. Build Enajenantes
    enajenantes_cop = []
    enajenante_unico = None
    if len(data.datos_enajenante) == 1 and data.datos_enajenante[0].copro_soc_conyugal_e == "No":
        enaj = data.datos_enajenante[0]
        n, ap, am = split_name(sanitize_name(enaj.nombre), enaj.apellido_paterno, enaj.apellido_materno)
        enajenante_unico = notariospublicos10.DatosUnEnajenante(
            nombre=n,
            apellido_paterno=ap,
            apellido_materno=am,
            rfc=enaj.rfc,
            curp=enaj.curp
        )
        datos_enajenante = notariospublicos10.DatosEnajenante(
            copro_soc_conyugal_e="No",
            datos_un_enajenante=enajenante_unico
        )
    else:
        for enaj in data.datos_enajenante:
            if enaj.copro_soc_conyugal_e == "No":
                raise ValueError("CoproSocConyugalE is 'No' but multiple Enajenantes found.")
            n, ap, am = split_name(sanitize_name(enaj.nombre), enaj.apellido_paterno, enaj.apellido_materno)
            enajenantes_cop.append(notariospublicos10.DatosEnajenanteCopSC(
                nombre=n,
                apellido_paterno=ap,
                apellido_materno=am,
                rfc=enaj.rfc,
                curp=enaj.curp,
                porcentaje=enaj.porcentaje
            ))
        datos_enajenante = notariospublicos10.DatosEnajenante(
            copro_soc_conyugal_e="Si",
            datos_enajenantes_cop_sc=enajenantes_cop
        )


    # Assemble
    complemento = notariospublicos10.NotariosPublicos(
        desc_inmuebles=desc_inmuebles,
        datos_operacion=datos_operacion,
        datos_notario=datos_notario,
        datos_enajenante=datos_enajenante,
        datos_adquiriente=datos_adquiriente
    )

    return complemento

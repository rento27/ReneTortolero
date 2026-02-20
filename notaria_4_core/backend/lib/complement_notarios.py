from datetime import date
from decimal import Decimal
from typing import List

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
from .api_models import ComplementoNotariosModel, DatosAdquiriente as AdqModel, DatosEnajenante as EnajModel

def split_name(full_name: str) -> dict:
    parts = full_name.strip().split()
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
    return {"nombre": full_name, "apellido_paterno": "", "apellido_materno": ""}

def create_complemento_notarios(data: ComplementoNotariosModel) -> NotariosPublicos:
    # 1. Validate Date
    if data.datos_operacion.fecha_inst_notarial > date.today():
        raise ValueError(f"Fecha de Instrumento Notarial cannot be in the future: {data.datos_operacion.fecha_inst_notarial}")

    # 2. Datos Notario
    # Using defaults from model if not provided, but ensuring they match prompt constants
    notario = DatosNotario(
        curp=data.datos_notario.curp,
        num_notaria=data.datos_notario.num_notaria,
        entidad_federativa=data.datos_notario.entidad_federativa,
        adscripcion=data.datos_notario.adscripcion
    )

    # 3. Datos Operacion
    operacion = DatosOperacion(
        num_instrumento_notarial=data.datos_operacion.num_instrumento_notarial,
        fecha_inst_notarial=data.datos_operacion.fecha_inst_notarial,
        monto_operacion=data.datos_operacion.monto_operacion,
        subtotal=data.datos_operacion.subtotal,
        iva=data.datos_operacion.iva
    )

    # 4. Inmuebles
    inmuebles = []
    for inm in data.desc_inmuebles:
        inmuebles.append(DescInmueble(
            tipo_inmueble=inm.tipo_inmueble,
            calle=inm.calle,
            municipio=inm.municipio,
            estado=inm.estado,
            pais=inm.pais,
            codigo_postal=inm.codigo_postal,
            no_exterior=inm.no_exterior,
            no_interior=inm.no_interior,
            colonia=inm.colonia,
            localidad=inm.localidad,
            referencia=inm.referencia
        ))

    # 5. Adquirientes logic
    adquirientes = _process_adquirientes(data.datos_adquirientes)

    # 6. Enajenantes logic
    enajenantes = None
    if data.datos_enajenantes:
        enajenantes = _process_enajenantes(data.datos_enajenantes)

    return NotariosPublicos(
        datos_notario=notario,
        datos_operacion=operacion,
        desc_inmuebles=inmuebles,
        datos_adquiriente=adquirientes,
        datos_enajenante=enajenantes
    )

def _process_adquirientes(adqs: List[AdqModel]):
    is_coproperty = len(adqs) > 1 or any(a.copro_soc_conyugal_e == 'Si' for a in adqs)

    if is_coproperty:
        # Validate sum 100%
        total = sum(a.porcentaje for a in adqs)
        if total != Decimal("100.00"):
             raise ValueError(f"Sum of percentages for Adquirientes must be 100.00, got {total}")

        lista_cop = []
        for a in adqs:
            names = split_name(a.nombre)
            # Override if explicit parts provided
            nom = a.nombre if a.apellido_paterno else names['nombre']
            pat = a.apellido_paterno if a.apellido_paterno else names['apellido_paterno']
            mat = a.apellido_materno if a.apellido_materno else names['apellido_materno']

            lista_cop.append(DatosAdquirienteCopSC(
                nombre=nom,
                apellido_paterno=pat,
                apellido_materno=mat,
                rfc=a.rfc,
                porcentaje=a.porcentaje
            ))
        return DatosAdquiriente(datos_adquirientes_cop_sc=lista_cop, copro_soc_conyugal_e='Si')
    else:
        # Single
        a = adqs[0]
        names = split_name(a.nombre)
        nom = a.nombre if a.apellido_paterno else names['nombre']
        pat = a.apellido_paterno if a.apellido_paterno else names['apellido_paterno']
        mat = a.apellido_materno if a.apellido_materno else names['apellido_materno']

        un_adq = DatosUnAdquiriente(
            nombre=nom,
            apellido_paterno=pat,
            apellido_materno=mat,
            rfc=a.rfc,
            curp=a.curp
        )
        return DatosAdquiriente(datos_un_adquiriente=un_adq, copro_soc_conyugal_e='No')

def _process_enajenantes(enajs: List[EnajModel]):
    is_coproperty = len(enajs) > 1 or any(e.copro_soc_conyugal_e == 'Si' for e in enajs)

    if is_coproperty:
        total = sum(e.porcentaje for e in enajs)
        if total != Decimal("100.00"):
             raise ValueError(f"Sum of percentages for Enajenantes must be 100.00, got {total}")

        lista_cop = []
        for e in enajs:
            names = split_name(e.nombre)
            nom = e.nombre if e.apellido_paterno else names['nombre']
            pat = e.apellido_paterno if e.apellido_paterno else names['apellido_paterno']
            mat = e.apellido_materno if e.apellido_materno else names['apellido_materno']

            lista_cop.append(DatosEnajenanteCopSC(
                nombre=nom,
                apellido_paterno=pat,
                apellido_materno=mat,
                rfc=e.rfc,
                porcentaje=e.porcentaje
            ))
        return DatosEnajenante(datos_enajenantes_cop_sc=lista_cop, copro_soc_conyugal_e='Si')
    else:
        e = enajs[0]
        names = split_name(e.nombre)
        nom = e.nombre if e.apellido_paterno else names['nombre']
        pat = e.apellido_paterno if e.apellido_paterno else names['apellido_paterno']
        mat = e.apellido_materno if e.apellido_materno else names['apellido_materno']

        un_enaj = DatosUnEnajenante(
            nombre=nom,
            apellido_paterno=pat,
            apellido_materno=mat,
            rfc=e.rfc,
            curp=e.curp
        )
        return DatosEnajenante(datos_un_enajenante=un_enaj, copro_soc_conyugal_e='No')

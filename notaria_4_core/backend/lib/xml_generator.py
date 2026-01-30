from decimal import Decimal
from satcfdi.create.cfd import cfdi40
from satcfdi.create.cfd.notariospublicos10 import NotariosPublicos, DatosNotario, DatosOperacion, DescInmueble, DatosAdquiriente, DatosEnajenante, DatosAdquirienteCopSC, DatosUnAdquiriente, DatosEnajenanteCopSC, DatosUnEnajenante
from .fiscal_engine import calculate_retentions, sanitize_name, validate_copropiedad, get_retention_rates, ROUNDING_MODE

def generar_complemento_notarios(datos_complemento: dict) -> NotariosPublicos:
    """
    Generates the 'Complemento de Notarios Públicos 1.0' object.

    Args:
        datos_complemento (dict): Dictionary containing all required data for the complement.

    Returns:
        NotariosPublicos: The satcfdi object for the complement.
    """

    # 1. DatosNotario
    dn_data = datos_complemento['DatosNotario']
    datos_notario = DatosNotario(
        curp=dn_data['CURP'],
        num_notaria=dn_data['NumNotaria'],
        entidad_federativa=dn_data['EntidadFederativa'],
        adscripcion=dn_data['Adscripcion']
    )

    # 2. DatosOperacion
    do_data = datos_complemento['DatosOperacion']
    datos_operacion = DatosOperacion(
        num_instrumento_notarial=do_data['NumInstrumentoNotarial'],
        fecha_inst_notarial=do_data['FechaInstNotarial'],
        monto_operacion=Decimal(do_data['MontoOperacion']),
        subtotal=Decimal(do_data['Subtotal']),
        iva=Decimal(do_data['IVA'])
    )

    # 3. DescInmuebles
    di_data = datos_complemento['DescInmuebles']
    desc_inmuebles = DescInmueble(
        tipo_inmueble=di_data['TipoInmueble'],
        calle=di_data['Calle'],
        municipio=di_data['Municipio'],
        estado=di_data['Estado'],
        pais=di_data['Pais'],
        codigo_postal=di_data['CodigoPostal']
    )

    # Helper to process subjects (Adquirientes/Enajenantes)
    def process_subjects(input_list, is_adquiriente=True):
        is_copropiedad = False
        if len(input_list) > 1:
            is_copropiedad = True
        elif len(input_list) == 1:
            if is_adquiriente and 'DatosAdquirientesCopSC' in input_list[0]:
                is_copropiedad = True
            elif not is_adquiriente and 'DatosEnajenantesCopSC' in input_list[0]:
                is_copropiedad = True

        if is_copropiedad:
            copro_sc_list = []
            percentages = []
            for item in input_list:
                cop_key = 'DatosAdquirientesCopSC' if is_adquiriente else 'DatosEnajenantesCopSC'
                cop_data = item.get(cop_key, item)
                percentage = Decimal(cop_data.get('Porcentaje', '0'))
                percentages.append(percentage)

                common_kwargs = {
                    'nombre': sanitize_name(cop_data['Nombre']),
                    'rfc': cop_data['RFC'],
                    'porcentaje': percentage,
                    'apellido_paterno': sanitize_name(cop_data.get('ApellidoPaterno')),
                    'apellido_materno': sanitize_name(cop_data.get('ApellidoMaterno')),
                    'curp': cop_data.get('CURP')
                }

                if is_adquiriente:
                    copro_sc_list.append(DatosAdquirienteCopSC(**common_kwargs))
                else:
                    copro_sc_list.append(DatosEnajenanteCopSC(**common_kwargs))

            if not validate_copropiedad(percentages):
                subject_type = "adquirientes" if is_adquiriente else "enajenantes"
                raise ValueError(f"La suma de porcentajes de copropiedad ({subject_type}) no es 100.00%: {sum(percentages)}")

            MainClass = DatosAdquiriente if is_adquiriente else DatosEnajenante
            key_arg = 'datos_adquirientes_cop_sc' if is_adquiriente else 'datos_enajenantes_cop_sc'
            return MainClass(copro_soc_conyugal_e="Si", **{key_arg: copro_sc_list})

        else:
            # Single
            if not input_list:
                return None

            item = input_list[0]

            if is_adquiriente:
                un_data = DatosUnAdquiriente(
                    nombre=sanitize_name(item['Nombre']),
                    rfc=item['RFC'],
                    apellido_paterno=sanitize_name(item.get('ApellidoPaterno')),
                    apellido_materno=sanitize_name(item.get('ApellidoMaterno')),
                    curp=item.get('CURP')
                )
                return DatosAdquiriente(copro_soc_conyugal_e="No", datos_un_adquiriente=un_data)
            else:
                un_data = DatosUnEnajenante(
                    nombre=sanitize_name(item['Nombre']),
                    apellido_paterno=sanitize_name(item['ApellidoPaterno']),
                    rfc=item['RFC'],
                    curp=item['CURP'],
                    apellido_materno=sanitize_name(item.get('ApellidoMaterno'))
                )
                return DatosEnajenante(copro_soc_conyugal_e="No", datos_un_enajenante=un_data)

    # 4. DatosAdquirientes
    datos_adquirientes = process_subjects(datos_complemento.get('DatosAdquirientes', []), is_adquiriente=True)
    if not datos_adquirientes:
         raise ValueError("DatosAdquirientes is mandatory")

    # 5. DatosEnajenantes
    datos_enajenantes = process_subjects(datos_complemento.get('DatosEnajenantes', []), is_adquiriente=False)
    if not datos_enajenantes:
         raise ValueError("DatosEnajenantes is mandatory")

    # Construct the main Complement object
    complemento = NotariosPublicos(
        datos_notario=datos_notario,
        datos_operacion=datos_operacion,
        desc_inmuebles=desc_inmuebles,
        datos_adquiriente=datos_adquirientes,
        datos_enajenante=datos_enajenantes
    )

    return complemento

def generar_factura(datos_factura: dict, datos_complemento: dict = None, signer=None) -> cfdi40.Comprobante:
    """
    Generates the CFDI 4.0 XML.

    Args:
        datos_factura (dict): Standard CFDI data (Emisor, Receptor, Conceptos).
        datos_complemento (dict): Data for the Notarios Publicos complement.
        signer (Signer): The signer object loaded from Secret Manager.

    Returns:
        cfdi40.Comprobante: The generated CFDI object.
    """

    rfc_receptor = datos_factura['Receptor']['Rfc']
    # Use logic from fiscal engine to determine rates
    retention_rates = get_retention_rates(rfc_receptor)

    processed_concepts = []

    for concepto_data in datos_factura['Conceptos']:
        c = concepto_data.copy()

        # Ensure Numeric types are Decimal
        # This fixes "TypeError: can't multiply sequence by non-int of type 'str'"
        if 'Cantidad' in c:
            c['Cantidad'] = Decimal(c['Cantidad'])
        if 'ValorUnitario' in c:
            c['ValorUnitario'] = Decimal(c['ValorUnitario'])
        if 'Importe' in c:
            c['Importe'] = Decimal(c['Importe'])
        if 'Descuento' in c:
            c['Descuento'] = Decimal(c['Descuento'])

        # If ObjetoImp is 02, add taxes
        if c.get('ObjetoImp') == '02':
            base = c['Importe'] # Base is typically Importe (Cantidad * ValorUnitario - Descuento)

            traslados = [
                {'Impuesto': '002', 'TipoFactor': 'Tasa', 'TasaOCuota': '0.160000',
                 'Importe': (base * Decimal("0.16")).quantize(Decimal("0.01"), rounding=ROUNDING_MODE),
                 'Base': base}
            ]

            impuestos_concepto = {'Traslados': traslados}

            if retention_rates:
                retenciones = []
                # ISR
                if 'isr' in retention_rates:
                    retenciones.append({
                        'Impuesto': '001',
                        'TipoFactor': 'Tasa',
                        'TasaOCuota': '0.100000',
                        'Importe': (base * retention_rates['isr']).quantize(Decimal("0.01"), rounding=ROUNDING_MODE),
                        'Base': base
                    })
                # IVA
                if 'iva' in retention_rates:
                    retenciones.append({
                        'Impuesto': '002',
                        'TipoFactor': 'Tasa',
                        'TasaOCuota': '0.106667',
                        'Importe': (base * retention_rates['iva']).quantize(Decimal("0.01"), rounding=ROUNDING_MODE),
                        'Base': base
                    })

                impuestos_concepto['Retenciones'] = retenciones

            c['Impuestos'] = impuestos_concepto

        processed_concepts.append(c)

    # 2. Build Complement if provided
    complemento_node = None
    if datos_complemento:
        complemento_node = generar_complemento_notarios(datos_complemento)

    # 3. Build Comprobante
    # satcfdi automatically sums up taxes from concepts into global Impuestos and calculates SubTotal/Total
    cfdi = cfdi40.Comprobante(
        emisor=datos_factura['Emisor'],
        receptor=datos_factura['Receptor'],
        conceptos=processed_concepts,
        complemento=complemento_node,
        moneda=datos_factura.get('Moneda', 'MXN'),
        forma_pago=datos_factura.get('FormaPago', '03'),
        metodo_pago=datos_factura.get('MetodoPago', 'PUE'),
        lugar_expedicion=datos_factura.get('LugarExpedicion', '28200'),
        serie=datos_factura.get('Serie', ''),
        folio=datos_factura.get('Folio', '')
        # SubTotal and Total are calculated automatically by satcfdi
    )

    if signer:
        cfdi.sign(signer)

    return cfdi

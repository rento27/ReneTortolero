from decimal import Decimal
from satcfdi.create.cfd import cfdi40
from satcfdi.create.cfd.catalogos import RegimenFiscal, UsoCFDI, MetodoPago, FormaPago, TipoDeComprobante, Moneda
from .fiscal_engine import sanitize_name, get_retention_rates, validate_copropiedad, ROUNDING_MODE

class XMLGenerator:
    def __init__(self, signer=None):
        self.signer = signer

    def generate_cfdi(self, data: dict):
        # Sanitize Receptor Name
        receptor_name = sanitize_name(data['receptor']['nombre'])
        receptor_rfc = data['receptor']['rfc']

        # Calculate Retentions
        retention_rates = get_retention_rates(receptor_rfc)

        # Build Conceptos and Taxes
        conceptos = []
        total_traslados = Decimal("0.00")
        total_retenciones = Decimal("0.00")
        subtotal = Decimal("0.00")

        # Bases for global tax summary
        base_traslado_002 = Decimal("0.00")
        base_retencion_001 = Decimal("0.00")
        base_retencion_002 = Decimal("0.00")

        for item in data['conceptos']:
            importe = Decimal(str(item['importe']))
            valor_unitario = Decimal(str(item['valor_unitario']))
            cantidad = Decimal(str(item['cantidad']))

            # Logic for ObjetoImp
            # 02: Sí objeto de impuesto
            # 01: No objeto de impuesto
            objeto_imp = item.get('objeto_imp', '02')

            impuestos_concepto = None
            if objeto_imp == '02':
                # Base is Importe
                base = importe
                base_traslado_002 += base

                # Traslados (IVA 16%)
                iva_traslado = (base * Decimal("0.16")).quantize(Decimal("0.01"), rounding=ROUNDING_MODE)
                total_traslados += iva_traslado

                traslados_list = [
                    cfdi40.Traslado(
                        Base=base,
                        Impuesto='002',
                        TipoFactor='Tasa',
                        TasaOCuota=Decimal('0.160000'),
                        Importe=iva_traslado
                    )
                ]

                # Retentions (if applicable)
                retenciones_list = []
                if retention_rates['isr'] > 0:
                    isr_ret = (base * retention_rates['isr']).quantize(Decimal("0.01"), rounding=ROUNDING_MODE)
                    total_retenciones += isr_ret
                    base_retencion_001 += base
                    retenciones_list.append(
                        cfdi40.Retencion(
                            Base=base,
                            Impuesto='001', # ISR
                            TipoFactor='Tasa',
                            TasaOCuota=retention_rates['isr'],
                            Importe=isr_ret
                        )
                    )

                if retention_rates['iva'] > 0:
                    # IVA Retention is 2/3 of 0.16 = 0.106667
                    iva_ret = (base * retention_rates['iva']).quantize(Decimal("0.01"), rounding=ROUNDING_MODE)
                    total_retenciones += iva_ret
                    base_retencion_002 += base
                    retenciones_list.append(
                         cfdi40.Retencion(
                            Base=base,
                            Impuesto='002', # IVA
                            TipoFactor='Tasa',
                            TasaOCuota=retention_rates['iva'],
                            Importe=iva_ret
                        )
                    )

                impuestos_concepto = cfdi40.Impuestos(
                    Traslados=traslados_list,
                    Retenciones=retenciones_list if retenciones_list else None
                )

            conceptos.append(cfdi40.Concepto(
                ClaveProdServ=item['clave_prod_serv'],
                NoIdentificacion=item.get('no_identificacion'),
                Cantidad=cantidad,
                ClaveUnidad=item['clave_unidad'],
                Unidad=item.get('unidad'),
                Descripcion=item['descripcion'],
                ValorUnitario=valor_unitario,
                Importe=importe,
                ObjetoImp=objeto_imp,
                Impuestos=impuestos_concepto
            ))
            subtotal += importe

        # Global Taxes
        impuestos_global = None
        if total_traslados > 0 or total_retenciones > 0:
            traslados_global = []
            if total_traslados > 0:
                traslados_global.append(cfdi40.Traslado(
                    Base=base_traslado_002,
                    Impuesto='002',
                    TipoFactor='Tasa',
                    TasaOCuota=Decimal('0.160000'),
                    Importe=total_traslados
                ))

            retenciones_global = []
            if retention_rates['isr'] > 0:
                 retenciones_global.append(cfdi40.Retencion(
                    Impuesto='001',
                    Importe=(base_retencion_001 * retention_rates['isr']).quantize(Decimal("0.01"), rounding=ROUNDING_MODE)
                ))
            if retention_rates['iva'] > 0:
                 retenciones_global.append(cfdi40.Retencion(
                    Impuesto='002',
                    Importe=(base_retencion_002 * retention_rates['iva']).quantize(Decimal("0.01"), rounding=ROUNDING_MODE)
                ))

            impuestos_global = cfdi40.Impuestos(
                TotalImpuestosTrasladados=total_traslados if total_traslados > 0 else None,
                TotalImpuestosRetenidos=total_retenciones if total_retenciones > 0 else None,
                Traslados=traslados_global if traslados_global else None,
                Retenciones=retenciones_global if retenciones_global else None
            )

        # Complemento Notarios
        complemento = None
        if 'notario_data' in data:
            complemento = self.generar_complemento_notarios(data['notario_data'])

        cfdi = cfdi40.Comprobante(
            Emisor=cfdi40.Emisor(
                Rfc=data['emisor']['rfc'],
                Nombre=sanitize_name(data['emisor']['nombre']),
                RegimenFiscal=data['emisor']['regimen_fiscal']
            ),
            Receptor=cfdi40.Receptor(
                Rfc=receptor_rfc,
                Nombre=receptor_name,
                DomicilioFiscalReceptor=data['receptor']['codigo_postal'],
                RegimenFiscalReceptor=data['receptor']['regimen_fiscal'],
                UsoCFDI=data['receptor']['uso_cfdi']
            ),
            Conceptos=conceptos,
            Impuestos=impuestos_global,
            SubTotal=subtotal,
            Moneda=Moneda.MXN,
            Total=subtotal + total_traslados - total_retenciones,
            TipoDeComprobante=TipoDeComprobante.INGRESO,
            MetodoPago=MetodoPago.PAGO_EN_UNA_SOLA_EXHIBICION,
            LugarExpedicion=data['emisor']['lugar_expedicion'],
            Complemento=complemento
        )

        if self.signer:
            cfdi.sign(self.signer)

        return cfdi

    def generar_complemento_notarios(self, data):
        # Validation of copropiedad
        if 'adquirientes' in data:
            percentages = [Decimal(str(a['porcentaje'])) for a in data['adquirientes']]
            if not validate_copropiedad(percentages):
                raise ValueError("La suma de los porcentajes de copropiedad no es 100.00%")

        # We assume the library satcfdi handles the XML structure if we provide the correct dict
        # Or we return a dictionary that satcfdi can embed.
        # This part assumes a custom implementation or generic dictionary support.

        return {
            "notariospublicos:NotariosPublicos": {
                "Version": "1.0",
                "DatosNotario": {
                    "NumNotaria": 4,
                    "EntidadFederativa": "06",
                    "Adscripcion": "MANZANILLO COLIMA"
                },
                "DatosOperacion": {
                    "FechaInstNotarial": data['fecha_instrumento'],
                    "MontoOperacion": data['monto_operacion'],
                    "SubTotal": data['subtotal'],
                    "IVA": data['iva']
                },
                "DatosNotarial": {
                    "DatosAdquirientes": {
                        "DatosAdquirientesCopSC": [
                            {
                                "Nombre": sanitize_name(a['nombre']),
                                "ApellidoPaterno": a['apellido_paterno'],
                                "ApellidoMaterno": a.get('apellido_materno', ''),
                                "RFC": a['rfc'],
                                "Porcentaje": a['porcentaje']
                            } for a in data['adquirientes']
                        ]
                    }
                }
            }
        }

from decimal import Decimal
from satcfdi.create.cfd import cfdi40
from satcfdi.create.cfd.complemento.notariospublicos import NotariosPublicos, DatosNotario, DatosOperacion, DatosInmueble, DatosAdquirientesCopSC
from satcfdi.models import Signer
# Note: Google Secret Manager would be imported here in prod
# from google.cloud import secretmanager

class XMLGenerator:
    @staticmethod
    def load_signer_from_secrets(project_id: str, secret_version: str = "latest"):
        """
        Retrieves the CSD certificate and key from Google Secret Manager.
        This is a placeholder implementation that would connect to GCP in production.
        """
        raise NotImplementedError("GCP Secret Manager access is not configured in this environment.")

    @staticmethod
    def generate_notary_complement(
        fecha_inst: str,
        num_instrumento: int,
        monto_operacion: Decimal,
        subtotal: Decimal,
        iva: Decimal,
        desc_inmuebles: list,
        adquirientes: list = None
    ) -> NotariosPublicos:
        """
        Generates the 'Complemento de Notarios Públicos'.

        Args:
            fecha_inst: Date of the instrument (YYYY-MM-DD).
            num_instrumento: Notarial instrument number.
            monto_operacion: Value of the operation.
            subtotal: Subtotal of the invoice.
            iva: IVA of the invoice.
            desc_inmuebles: List of dicts describing properties (TipoInmueble, Calle, etc).
            adquirientes: List of dicts for Copropiedad (if applicable).
                          Each dict: {'Nombre': str, 'ApellidoPaterno': str, 'ApellidoMaterno': str, 'Rfc': str, 'Porcentaje': Decimal}
        """

        # 1. DatosNotario (Constants for Notaria 4)
        datos_notario = DatosNotario(
            NumNotaria=4,
            EntidadFederativa="06", # Colima
            Adscripcion="MANZANILLO, COLIMA"
        )

        # 2. DatosOperacion
        datos_operacion = DatosOperacion(
            NumInstrumentoNotarial=num_instrumento,
            FechaInstNotarial=fecha_inst,
            MontoOperacion=monto_operacion,
            Subtotal=subtotal,
            IVA=iva
        )

        # 3. DatosInmueble
        # Assuming desc_inmuebles contains the required fields
        inmuebles = []
        for inm in desc_inmuebles:
            inmuebles.append(DatosInmueble(**inm))

        datos_operacion["DatosInmueble"] = inmuebles

        # 4. DatosAdquirientes (Copropiedad)
        if adquirientes:
            coproperietarios = []
            for adq in adquirientes:
                coproperietarios.append(DatosAdquirientesCopSC(**adq))

            # According to logic, sum must be checked (done in FiscalEngine usually),
            # here we just attach the node.
            datos_operacion["DatosAdquirientes"] = {"DatosAdquirientesCopSC": coproperietarios}

        # Create Complemento
        complemento = NotariosPublicos(
            DatosNotario=datos_notario,
            DatosOperacion=datos_operacion
        )

        return complemento

    @staticmethod
    def generate_invoice_xml(
        emisor_data: dict,
        receptor_data: dict,
        items: list,
        payment_form: str = "99",
        payment_method: str = "PPD",
        signer: Signer = None,
        notary_data: dict = None
    ) -> cfdi40.Comprobante:
        """
        Generates a CFDI 4.0 object based on the provided data.
        """

        conceptos = []
        subtotal = Decimal('0.00')
        total_impuestos_trasladados = Decimal('0.00')
        total_impuestos_retenidos = Decimal('0.00')

        # Calculate totals and build Concepts
        for item in items:
            importe = Decimal(str(item['ValorUnitario'])) * Decimal(str(item['Cantidad']))
            subtotal += importe

            concepto_args = {
                "ClaveProdServ": item['ClaveProdServ'],
                "Cantidad": Decimal(str(item['Cantidad'])),
                "ClaveUnidad": item['ClaveUnidad'],
                "Descripcion": item['Descripcion'],
                "ValorUnitario": Decimal(str(item['ValorUnitario'])),
                "Importe": importe,
                "ObjetoImp": item['ObjetoImp']
            }

            # Add Taxes to Concept if ObjetoImp is '02'
            if item['ObjetoImp'] == '02':
                # Standard IVA 16%
                base = importe
                impuesto_importe = base * Decimal('0.16')
                total_impuestos_trasladados += impuesto_importe

                traslados = cfdi40.Traslados(
                    Traslado=cfdi40.Traslado(
                        Base=base,
                        Impuesto='002', # IVA
                        TipoFactor='Tasa',
                        TasaOCuota=Decimal('0.160000'),
                        Importe=impuesto_importe
                    )
                )
                concepto_args['Impuestos'] = cfdi40.Impuestos(Traslados=traslados)

            conceptos.append(cfdi40.Concepto(**concepto_args))

        # Taxes Global
        impuestos_globales = None
        if total_impuestos_trasladados > 0:
            impuestos_globales = cfdi40.Impuestos(
                TotalImpuestosTrasladados=total_impuestos_trasladados,
                Traslados=[
                    cfdi40.TrasladoGlobal(
                        Impuesto='002',
                        TipoFactor='Tasa',
                        TasaOCuota=Decimal('0.160000'),
                        Importe=total_impuestos_trasladados
                    )
                ]
            )

        # Complement
        complemento_node = None
        if notary_data:
            complemento_node = XMLGenerator.generate_notary_complement(
                fecha_inst=notary_data['fecha_inst'],
                num_instrumento=notary_data['num_instrumento'],
                monto_operacion=Decimal(str(notary_data['monto_operacion'])),
                subtotal=subtotal,
                iva=total_impuestos_trasladados,
                desc_inmuebles=notary_data['inmuebles'],
                adquirientes=notary_data.get('adquirientes')
            )

        # Create Comprobante
        cfdi = cfdi40.Comprobante(
            Emisor=cfdi40.Emisor(**emisor_data),
            Receptor=cfdi40.Receptor(**receptor_data),
            Conceptos=conceptos,
            Impuestos=impuestos_globales,
            Complemento=complemento_node,
            SubTotal=subtotal,
            Moneda='MXN',
            Total=subtotal + total_impuestos_trasladados - total_impuestos_retenidos, # Simplified
            TipoDeComprobante='I',
            Exportacion='01', # No aplica
            MetodoPago=payment_method,
            FormaPago=payment_form,
            LugarExpedicion=emisor_data.get('LugarExpedicion', '28200') # Manzanillo default
        )

        if signer:
            cfdi.sign(signer)

        return cfdi

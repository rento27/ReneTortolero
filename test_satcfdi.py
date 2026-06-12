from satcfdi.create.cfd import cfdi40

try:
    cfdi_kwargs = {'emisor': {}, 'receptor': {}, 'conceptos': [], 'lugar_expedicion': '12345'}
    cfdi = cfdi40.Comprobante(**cfdi_kwargs)
    print(hasattr(cfdi, 'add_complemento'))
except Exception as e:
    print(f"Error: {e}")

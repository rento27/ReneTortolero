from satcfdi.create.cfd import notariospublicos10

adq = notariospublicos10.DatosAdquiriente(
    copro_soc_conyugal_e='Si',
    datos_adquirientes_cop_sc=[]
)
print("Adquiriente created successfully.")

desc = notariospublicos10.DescInmueble(
    tipo_inmueble='01',
    calle='Calle 1',
    estado='COL',
    pais='MEX',
    codigo_postal='28200',
    municipio='Manzanillo'
)
print("DescInmueble created successfully.")

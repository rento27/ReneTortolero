import weasyprint

def generate_hybrid_pdf(xml_bytes: bytes, invoice_data: dict) -> bytes:
    """
    Generates a PDF that acts as a hybrid 'Cuenta de Gastos' by displaying
    both the fiscal information from the XML and the non-fiscal administrative charges.

    This is a stub implementation that just returns a basic PDF document.
    """
    html_content = f"""
    <html>
        <head>
            <title>Cuenta de Gastos y CFDI</title>
            <style>
                body {{ font-family: sans-serif; }}
                h1 {{ color: #1a202c; }}
                .section {{ margin-bottom: 20px; }}
            </style>
        </head>
        <body>
            <h1>Notaría 4 - Manzanillo, Colima</h1>
            <h2>Cuenta de Gastos y Comprobante Fiscal Digital</h2>

            <div class="section">
                <h3>Datos del Cliente</h3>
                <p><strong>Nombre:</strong> {invoice_data.get('receptor', {{}}).get('nombre', 'N/A')}</p>
                <p><strong>RFC:</strong> {invoice_data.get('receptor', {{}}).get('rfc', 'N/A')}</p>
            </div>

            <div class="section">
                <h3>Resumen Fiscal</h3>
                <p><strong>Subtotal:</strong> ${invoice_data.get('subtotal', 0.00)}</p>
                <p><strong>Total:</strong> ${invoice_data.get('total', 0.00)}</p>
            </div>

            <div class="section">
                <h3>Otros Gastos Administrativos (No Fiscales)</h3>
                <p><em>Esta sección incluye derechos e impuestos locales procesados.</em></p>
            </div>
        </body>
    </html>
    """

    pdf_bytes = weasyprint.HTML(string=html_content).write_pdf()
    return pdf_bytes

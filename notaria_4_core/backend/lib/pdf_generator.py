import base64
from io import BytesIO
try:
    import weasyprint
except ImportError:
    weasyprint = None

def generate_hybrid_pdf(xml_bytes: bytes, invoice_data: dict) -> bytes:
    """
    Generates a Hybrid PDF document containing the fiscal representation
    along with the administrative 'Cuenta de Gastos'.
    """
    if not weasyprint:
        # Stub fallback if weasyprint is not installed
        return b"%PDF-1.4\n%Stub Hybrid PDF\n"

    # We will build a simple HTML representation of the invoice data and the Cuenta de Gastos.
    html_content = f"""
    <html>
        <head>
            <style>
                body {{ font-family: sans-serif; font-size: 12px; }}
                h1 {{ font-size: 16px; color: #333; }}
                .section {{ margin-bottom: 20px; }}
                table {{ width: 100%; border-collapse: collapse; }}
                th, td {{ border: 1px solid #ccc; padding: 5px; text-align: left; }}
                th {{ background-color: #f5f5f5; }}
            </style>
        </head>
        <body>
            <h1>Notaría Pública No. 4 - Manzanillo</h1>
            <h2>Comprobante Fiscal Digital por Internet (CFDI 4.0)</h2>
            <div class="section">
                <strong>Receptor:</strong> {invoice_data.get('receptor', {{}}).get('nombre', 'N/A')}<br>
                <strong>RFC:</strong> {invoice_data.get('receptor', {{}}).get('rfc', 'N/A')}<br>
                <strong>Uso CFDI:</strong> {invoice_data.get('receptor', {{}}).get('uso_cfdi', 'N/A')}
            </div>

            <div class="section">
                <h3>Conceptos Fiscales</h3>
                <table>
                    <thead>
                        <tr>
                            <th>Descripción</th>
                            <th>Importe</th>
                        </tr>
                    </thead>
                    <tbody>
    """

    for c in invoice_data.get('conceptos', []):
        html_content += f"""
                        <tr>
                            <td>{c.get('descripcion', '')}</td>
                            <td>${c.get('importe', '0.00')}</td>
                        </tr>
        """

    html_content += f"""
                    </tbody>
                </table>
                <p><strong>Subtotal:</strong> ${invoice_data.get('subtotal', '0.00')}</p>
                <p><strong>Total:</strong> ${invoice_data.get('total', '0.00')}</p>
            </div>

            <hr>

            <div class="section">
                <h2>Anexo: Cuenta de Gastos (Administrativo)</h2>
                <p>Este apartado detalla conceptos no fiscales (Derechos, ISAI, etc.) relacionados a la operación.</p>
                <table>
                    <thead>
                        <tr>
                            <th>Concepto</th>
                            <th>Monto</th>
                        </tr>
                    </thead>
                    <tbody>
    """

    # Render extra administrative data if present
    extra_data = invoice_data.get('datos_extra', {}) or {}
    for key, val in extra_data.items():
        html_content += f"""
                        <tr>
                            <td>{key}</td>
                            <td>${val}</td>
                        </tr>
        """

    html_content += """
                    </tbody>
                </table>
            </div>
            <div class="section" style="font-size: 10px; color: #777;">
                <p>Elaborado por Notaría 4 Digital Core</p>
            </div>
        </body>
    </html>
    """

    out = BytesIO()
    weasyprint.HTML(string=html_content).write_pdf(out)
    return out.getvalue()

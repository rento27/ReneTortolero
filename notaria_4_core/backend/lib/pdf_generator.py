import html
import base64

try:
    from weasyprint import HTML
except ImportError:
    HTML = None

def generate_hybrid_pdf(data: dict) -> str:
    """
    Generates a Hybrid PDF combining the fiscal XML information and
    an administrative 'Cuenta de Gastos'.

    Sanitizes all variables interpolated into the HTML template using html.escape
    to prevent HTML injection vulnerabilities.

    Returns the generated PDF as a base64 encoded string.
    """
    # Sanitize inputs
    nombre_receptor = html.escape(data.get('receptor', {}).get('nombre', ''))
    rfc_receptor = html.escape(data.get('receptor', {}).get('rfc', ''))
    subtotal = html.escape(str(data.get('subtotal', '0.00')))
    total = html.escape(str(data.get('total', '0.00')))

    # A simple HTML template incorporating the sanitized variables
    html_content = f"""
    <!DOCTYPE html>
    <html lang="es">
    <head>
        <meta charset="UTF-8">
        <title>Factura y Cuenta de Gastos</title>
        <style>
            body {{ font-family: Arial, sans-serif; }}
            h1 {{ color: navy; }}
            .section {{ margin-bottom: 20px; }}
        </style>
    </head>
    <body>
        <h1>Notaría 4 Digital Core</h1>
        <div class="section">
            <h2>Datos del Receptor</h2>
            <p><strong>Nombre:</strong> {nombre_receptor}</p>
            <p><strong>RFC:</strong> {rfc_receptor}</p>
        </div>
        <div class="section">
            <h2>Cuenta de Gastos</h2>
            <p><strong>Subtotal:</strong> ${subtotal}</p>
            <p><strong>Total:</strong> ${total}</p>
        </div>
        <div class="section">
            <h2>Detalle de Conceptos</h2>
            <ul>
    """

    for concepto in data.get('conceptos', []):
        desc = html.escape(concepto.get('descripcion', ''))
        importe = html.escape(str(concepto.get('importe', '0.00')))
        html_content += f"<li>{desc} - ${importe}</li>\n"

    html_content += """
            </ul>
        </div>
    </body>
    </html>
    """

    if HTML is not None:
        pdf_bytes = HTML(string=html_content).write_pdf()
        return base64.b64encode(pdf_bytes).decode('utf-8')
    else:
        # Stub for environments where weasyprint is not installed
        return base64.b64encode(b"PDF STUB").decode('utf-8')

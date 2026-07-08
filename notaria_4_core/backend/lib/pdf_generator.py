import html
import base64
from io import BytesIO

try:
    import weasyprint
except ImportError:
    weasyprint = None

def generate_hybrid_pdf(invoice_data: dict, xml_bytes: bytes) -> bytes:
    """
    Generates a Hybrid PDF document combining the fiscal XML data and an administrative 'Cuenta de Gastos'.
    Uses weasyprint for PDF generation and html.escape for sanitization.
    """
    if not weasyprint:
        # Return empty bytes if not installed
        return b""

    # Extract data for the template
    receptor = invoice_data.get('receptor', {})
    nombre = html.escape(receptor.get('nombre', ''))
    rfc = html.escape(receptor.get('rfc', ''))

    subtotal = invoice_data.get('subtotal', 0)
    total = invoice_data.get('total', 0)

    # Constructing a basic HTML representation
    html_content = f"""
    <!DOCTYPE html>
    <html lang="es">
    <head>
        <meta charset="UTF-8">
        <title>Comprobante Fiscal - Cuenta de Gastos</title>
        <style>
            body {{ font-family: Arial, sans-serif; margin: 40px; color: #333; }}
            .header {{ text-align: center; margin-bottom: 30px; }}
            .title {{ font-size: 24px; font-weight: bold; color: #1a365d; }}
            .section {{ margin-bottom: 20px; }}
            .label {{ font-weight: bold; }}
            .table {{ width: 100%; border-collapse: collapse; margin-top: 15px; }}
            .table th, .table td {{ border: 1px solid #ccc; padding: 8px; text-align: left; }}
            .table th {{ background-color: #f3f4f6; }}
            .cuenta-gastos {{ background-color: #e5e7eb; padding: 15px; border-radius: 5px; margin-top: 30px; }}
            .total-row {{ font-weight: bold; }}
        </style>
    </head>
    <body>
        <div class="header">
            <div class="title">NOTARIA PÚBLICA NO. 4</div>
            <div>Manzanillo, Colima</div>
        </div>

        <div class="section">
            <p><span class="label">Receptor:</span> {nombre}</p>
            <p><span class="label">RFC:</span> {rfc}</p>
        </div>

        <div class="section">
            <h3>Conceptos Fiscales</h3>
            <table class="table">
                <thead>
                    <tr>
                        <th>Descripción</th>
                        <th>Importe</th>
                    </tr>
                </thead>
                <tbody>
    """

    for concepto in invoice_data.get('conceptos', []):
        desc = html.escape(concepto.get('descripcion', ''))
        importe = html.escape(str(concepto.get('importe', '')))
        html_content += f"""
                    <tr>
                        <td>{desc}</td>
                        <td>${importe}</td>
                    </tr>
        """

    html_content += f"""
                </tbody>
            </table>
        </div>

        <div class="cuenta-gastos section">
            <h3>Anexo: Cuenta de Gastos (No Fiscal)</h3>
            <p>Se detallan a continuación los cobros administrativos y derechos adicionales asociados a su expediente.</p>
            <table class="table">
                <tr>
                    <td>Subtotal Fiscal</td>
                    <td>${html.escape(str(subtotal))}</td>
                </tr>
                <tr class="total-row">
                    <td>Total Operación</td>
                    <td>${html.escape(str(total))}</td>
                </tr>
            </table>
        </div>
    </body>
    </html>
    """

    # Generate PDF
    pdf = weasyprint.HTML(string=html_content).write_pdf()
    return pdf

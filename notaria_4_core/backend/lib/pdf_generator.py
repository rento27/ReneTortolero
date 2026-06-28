import html
import logging
from decimal import Decimal

try:
    from weasyprint import HTML
except ImportError:
    HTML = None

logger = logging.getLogger(__name__)

def generate_hybrid_pdf(xml_bytes: bytes, invoice_data: dict) -> bytes:
    """
    Generates a Hybrid PDF using weasyprint, combining the fiscal XML
    (represented as HTML for the PDF) and an administrative 'Cuenta de Gastos'.

    Args:
        xml_bytes (bytes): The signed CFDI XML data.
        invoice_data (dict): The dictionary containing invoice data.

    Returns:
        bytes: The generated PDF as bytes.
    """
    if HTML is None:
        logger.error("weasyprint is not installed. Returning mock PDF bytes.")
        return b"%PDF-1.4 Mock PDF Document"

    # 1. Build a simple HTML structure for the Hybrid PDF
    html_content = f"""
    <html>
    <head>
        <title>Notaría 4 - CFDI y Cuenta de Gastos</title>
        <style>
            body {{ font-family: Arial, sans-serif; }}
            .header {{ text-align: center; font-weight: bold; margin-bottom: 20px; }}
            .section {{ margin-top: 20px; padding: 10px; border: 1px solid #ccc; }}
            .title {{ font-size: 1.2em; font-weight: bold; margin-bottom: 10px; }}
            table {{ width: 100%; border-collapse: collapse; }}
            th, td {{ border: 1px solid #ddd; padding: 8px; text-align: left; }}
        </style>
    </head>
    <body>
        <div class="header">
            NOTARÍA PÚBLICA No. 4 - MANZANILLO<br>
            Comprobante Fiscal (CFDI 4.0) y Cuenta de Gastos
        </div>

        <div class="section">
            <div class="title">Datos Fiscales (CFDI)</div>
            <p><strong>Receptor RFC:</strong> {html.escape(str(invoice_data.get('receptor', {}).get('rfc', 'N/A')))}</p>
            <p><strong>Receptor Nombre:</strong> {html.escape(str(invoice_data.get('receptor', {}).get('nombre', 'N/A')))}</p>
            <p><strong>Subtotal:</strong> ${html.escape(str(invoice_data.get('subtotal', '0.00')))}</p>
            <p><strong>Total:</strong> ${html.escape(str(invoice_data.get('total', '0.00')))}</p>
            <!-- In a real app, parse XML and display CFDI details/QR Code here -->
            <p>XML Generado Exitosamente (Tamaño: {len(xml_bytes)} bytes)</p>
        </div>

        <div class="section">
            <div class="title">Anexo: Cuenta de Gastos Administrativos</div>
            <table>
                <tr>
                    <th>Concepto</th>
                    <th>Importe</th>
                </tr>
    """

    # Extract concepts for "Cuenta de Gastos"
    # Typically, these might include "Otros Derechos" or "Suplidos"
    conceptos = invoice_data.get('conceptos', [])
    for concepto in conceptos:
        desc = html.escape(str(concepto.get('descripcion', 'N/A')))
        importe = html.escape(str(concepto.get('importe', '0.00')))
        html_content += f"""
                <tr>
                    <td>{desc}</td>
                    <td>${importe}</td>
                </tr>
        """

    html_content += """
            </table>
        </div>
    </body>
    </html>
    """

    # 2. Render to PDF
    try:
        pdf_bytes = HTML(string=html_content).write_pdf()
        return pdf_bytes
    except Exception as e:
        logger.error(f"Error generating PDF with weasyprint: {e}")
        raise

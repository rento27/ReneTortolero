import logging
from typing import Optional

try:
    from weasyprint import HTML, CSS
except ImportError:
    HTML = None
    CSS = None

logger = logging.getLogger(__name__)

def generate_hybrid_pdf(xml_bytes: bytes, invoice_data: dict) -> bytes:
    """
    Generates a Hybrid PDF combining the fiscal XML representation
    with an administrative 'Anexo: Cuenta de Gastos' using WeasyPrint.
    """
    if not HTML:
        logger.error("WeasyPrint is not installed. PDF generation disabled.")
        return b""

    try:
        # Very basic stub HTML representation
        html_content = f"""
        <html>
            <head>
                <style>
                    body {{ font-family: sans-serif; }}
                    h1 {{ color: #333; }}
                    .fiscal {{ border-bottom: 1px solid #ccc; padding-bottom: 20px; }}
                    .anexo {{ margin-top: 20px; }}
                </style>
            </head>
            <body>
                <div class="fiscal">
                    <h1>Factura CFDI 4.0</h1>
                    <p>Receptor: {invoice_data.get('receptor', {{}}).get('nombre', '')}</p>
                    <p>Subtotal: ${invoice_data.get('subtotal', '0.00')}</p>
                    <p>Total Fiscal: ${invoice_data.get('total', '0.00')}</p>
                </div>
                <div class="anexo">
                    <h2>Anexo: Cuenta de Gastos</h2>
                    <p>Derechos de Registro: $300.00</p>
                    <p>ISAI: $30,000.00</p>
                    <p>Total Administrativo: $30,300.00</p>
                </div>
            </body>
        </html>
        """

        pdf_bytes = HTML(string=html_content).write_pdf()
        return pdf_bytes
    except Exception as e:
        logger.error(f"Error generating Hybrid PDF: {e}")
        return b""

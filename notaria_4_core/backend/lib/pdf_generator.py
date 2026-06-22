import os
import io
import base64
import tempfile
import weasyprint

def generate_hybrid_pdf(xml_bytes: bytes, invoice_data: dict) -> bytes:
    """
    Generates a Hybrid PDF using WeasyPrint.
    Combines the fiscal data (from invoice_data/xml) and an administrative 'Cuenta de Gastos'.
    Returns the PDF content as bytes.
    """
    # Very basic HTML generation for the PDF, demonstrating the required sections
    html_content = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <title>Notaria 4 Digital Core - CFDI y Cuenta de Gastos</title>
        <style>
            body {{ font-family: Arial, sans-serif; font-size: 12px; color: #333; }}
            .header {{ background-color: #002244; color: white; padding: 10px; text-align: center; }}
            .section {{ margin-top: 20px; }}
            .title {{ font-weight: bold; font-size: 14px; border-bottom: 1px solid #ccc; margin-bottom: 5px; }}
            table {{ width: 100%; border-collapse: collapse; }}
            th, td {{ border: 1px solid #ccc; padding: 5px; text-align: left; }}
        </style>
    </head>
    <body>
        <div class="header">
            <h1>Notaría Pública No. 4 - Manzanillo</h1>
            <h2>Lic. René Manuel Tortolero Santillana</h2>
        </div>

        <div class="section">
            <div class="title">Datos Fiscales (CFDI)</div>
            <p><strong>Receptor:</strong> {invoice_data.get('receptor', {{}}).get('nombre', '')}</p>
            <p><strong>RFC:</strong> {invoice_data.get('receptor', {{}}).get('rfc', '')}</p>
            <p><strong>Subtotal:</strong> ${invoice_data.get('subtotal', '0.00')}</p>
            <p><strong>Total:</strong> ${invoice_data.get('total', '0.00')}</p>
        </div>

        <div class="section">
            <div class="title">Anexo: Cuenta de Gastos</div>
            <table>
                <tr>
                    <th>Concepto</th>
                    <th>Importe</th>
                </tr>
    """

    for concepto in invoice_data.get('conceptos', []):
        html_content += f"""
                <tr>
                    <td>{concepto.get('descripcion', '')}</td>
                    <td>${concepto.get('importe', '0.00')}</td>
                </tr>
        """

    # Append any extra admin data as 'Otros Derechos'
    extra_data = invoice_data.get('datos_extra', {})
    if extra_data:
        html_content += f"""
                <tr>
                    <td>Otros Gastos Administrativos</td>
                    <td>(Detallado en Sistema)</td>
                </tr>
        """

    html_content += """
            </table>
        </div>
    </body>
    </html>
    """

    pdf_file = weasyprint.HTML(string=html_content).write_pdf()
    return pdf_file

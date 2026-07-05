import html
import hashlib
from datetime import datetime

try:
    from weasyprint import HTML
except ImportError:
    HTML = None

def generate_hybrid_pdf(data: dict, xml_bytes: bytes = None) -> bytes:
    """
    Generates a Hybrid PDF using weasyprint, combining the fiscal XML data
    and an administrative 'Cuenta de Gastos'.
    Escapes all interpolated variables to prevent HTML injection.
    """
    if not HTML:
        # Fallback if weasyprint is not available
        return b"%PDF-1.4 Mock Hybrid PDF"

    receptor_nombre = html.escape(data.get("receptor", {}).get("nombre", ""))
    receptor_rfc = html.escape(data.get("receptor", {}).get("rfc", ""))
    subtotal = html.escape(str(data.get("subtotal", "0.00")))
    total = html.escape(str(data.get("total", "0.00")))

    html_content = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <title>Factura y Cuenta de Gastos</title>
        <style>
            body {{ font-family: sans-serif; }}
            .header {{ text-align: center; margin-bottom: 20px; }}
            .fiscal, .gastos {{ margin-bottom: 30px; }}
            table {{ width: 100%; border-collapse: collapse; }}
            th, td {{ border: 1px solid #ccc; padding: 8px; text-align: left; }}
        </style>
    </head>
    <body>
        <div class="header">
            <h2>Notaría Pública No. 4 de Manzanillo, Colima</h2>
            <p>Lic. René Manuel Tortolero Santillana</p>
        </div>

        <div class="fiscal">
            <h3>Comprobante Fiscal Digital por Internet (CFDI)</h3>
            <p><strong>Receptor:</strong> {receptor_nombre}</p>
            <p><strong>RFC:</strong> {receptor_rfc}</p>
            <p><strong>Subtotal:</strong> ${subtotal}</p>
            <p><strong>Total:</strong> ${total}</p>
        </div>

        <div class="gastos">
            <h3>Anexo: Cuenta de Gastos</h3>
            <table>
                <tr>
                    <th>Concepto</th>
                    <th>Importe</th>
                </tr>
    """

    for concepto in data.get("conceptos", []):
        desc = html.escape(concepto.get("descripcion", ""))
        importe = html.escape(str(concepto.get("importe", "0.00")))
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

    try:
        pdf_bytes = HTML(string=html_content).write_pdf()
        return pdf_bytes
    except Exception as e:
        print(f"Error generating PDF with weasyprint: {e}")
        return b"%PDF-1.4 Mock Fallback PDF on error"

def generate_nom151_stamp(pdf_bytes: bytes) -> dict:
    """
    Generates a mock NOM-151 timestamp data hash by simulating an integration
    with a PSC (e.g., Mifiel, WeeSign).
    """
    if not pdf_bytes:
        pdf_bytes = b""

    pdf_hash = hashlib.sha256(pdf_bytes).hexdigest()
    timestamp = datetime.now().isoformat()

    # Return mock constancia
    return {
        "hash_sha256": pdf_hash,
        "timestamp": timestamp,
        "psc": "MockWeeSign",
        "valid": True,
        "message": "Constancia de Conservacion NOM-151 generada"
    }

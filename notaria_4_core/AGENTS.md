# Notaría 4 Digital Core - AGENTS.md

This file contains the architectural and operational guidelines for the "Notaría 4 Digital Core" project.

## Project Scope
A proprietary platform for Notaría Pública No. 4 in Manzanillo, Colima, utilizing a "Serverless Sovereign" architecture on Google Cloud Platform and Firebase.

## Architecture
- **Backend**: Python 3.11 with FastAPI running on Google Cloud Run.
- **Database**: Google Cloud Firestore (NoSQL).
- **Storage**: Google Cloud Storage for XML/PDFs.
- **Security**: Google Secret Manager for handling private keys and CSD passwords.

## Fiscal Rules & Validation (Critical)
1. **CFDI 4.0 Compliance**:
   - **Name Sanitization**: Remove corporate regimes (e.g., "S.A. DE C.V.") from names. Match SAT records exactly.
   - **Postal Code**: Validate `DomicilioFiscalReceptor` against `c_CodigoPostal`.
   - **ObjetoImp**:
     - `02` (Sí objeto de impuesto) for Honorarios.
     - `01` (No objeto de impuesto) or `ACuentaTerceros` for Suplidos/Gastos.

2. **Persona Moral Retentions**:
   - Trigger: RFC length is 12 characters.
   - **ISR Retention**: 10% of Tax Base.
   - **IVA Retention**: 2/3 of IVA (approx 10.6667%).
   - **Precision**: Use `decimal` library with extended precision to avoid rounding errors.

3. **ISAI Manzanillo**:
   - Formula: `Max(OperationPrice, CadastralValue) * Rate`.
   - Rate is configurable via Firebase Remote Config.

4. **Complemento de Notarios**:
   - **Copropiedad**: The sum of percentages in `DatosAdquirientesCopSC` must equal exactly 100.00%.
   - **Structure**: Follow `notariospublicos.xsd`.

## Coding Standards
- **Language**: Python 3.11.
- **Libraries**:
  - `satcfdi` for XML generation and signing.
  - `spacy` for NLP.
  - `pytesseract` / `fitz` (PyMuPDF) for OCR.
  - `fastapi` for the API.
- **Security**: NEVER hardcode secrets. Use the `signer.py` module to load from Secret Manager.

## Directory Structure
- `backend/`: FastAPI application.
- `backend/lib/`: Shared modules (`fiscal_engine.py`, `xml_generator.py`, `signer.py`).
- `backend/tests/`: Unit tests (`pytest`).

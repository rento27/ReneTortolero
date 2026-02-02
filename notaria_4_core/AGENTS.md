# AGENTS.md - Notaría 4 Digital Core Guidelines

## Context
Project: Notaría 4 Digital Core
Client: Notaría Pública No. 4 de Manzanillo, Colima (Lic. René Manuel Tortolero Santillana)
Goal: Replace 'TotalNot' with a sovereign, serverless platform on Firebase + Cloud Run.

## Architecture
- **Infrastructure**: "Serverless Sovereign" model.
    - **Backend**: Cloud Run (Python 3.11 Container) for heavy lifting (OCR, NLP, XML Signing).
    - **Frontend**: React (Vite) on Firebase Hosting.
    - **Database**: Cloud Firestore (NoSQL).
    - **Storage**: Cloud Storage (for PDF/XML).
    - **Secrets**: Google Secret Manager (CSD keys, API keys). **NEVER HARDCODE SECRETS.**
- **Eventing**: Firebase Cloud Functions (2nd Gen) for lightweight triggers (e.g., file upload -> Cloud Run).

## Fiscal & Business Rules (Strict Adherence Required)
### 1. CFDI 4.0 Validations
- **Name Sanitization**:
    - Receiver Name must match SAT records exactly but **exclude** the regime.
    - **Rule**: Use Regex to strip "S.A. DE C.V.", "S.C.", etc. from the input string before sending to PAC.
- **Zip Code**: Cross-reference `c_CodigoPostal` vs. Receiver's RFC.
- **ObjectImp**:
    - Honorarios: `02` (Sí objeto).
    - Suplidos/Derechos: `01` (No objeto) or `ACuentaTerceros`.

### 2. Tax Calculations (Engine Specs)
- **Persona Moral (RFC length == 12)**:
    - **ISR Retained**: 10.00% of Base.
    - **IVA Retained**: 10.6667% (2/3rds) of IVA Trasladado.
    - **Precision**: Use `decimal` library with high precision context to avoid off-by-one errors.
- **ISAI (Manzanillo)**:
    - **Formula**: `Max(OperationPrice, CatastralValue) * Tasa`.
    - **Tasa**: Loaded from Firebase Remote Config (initially ~3%).
- **Copropiedad**:
    - Sum of percentages in `DatosAdquirientesCopSC` must equal **100.00%** exactly.

## Technical Constraints
- **Python Stack**: `satcfdi` (XML), `spacy` (NLP), `pytesseract` (OCR), `pymupdf` (PDF Text), `fastapi`.
- **System Dependencies**: Container must install `tesseract-ocr`, `libgl1`, `libglib2.0-0`.
- **Environment**: Do not use `file://` paths for logic; assume cloud environment (Storage buckets).
- **Security**:
    - Documents locked when status == "Timbrado".
    - `Signer` loaded from memory bytes via Secret Manager.

## Operational
- **Shadow Mode**: System must be capable of running parallel to legacy system for verification.
- **Human-in-the-Loop**: UI must allow verification of extracted data against the PDF source.

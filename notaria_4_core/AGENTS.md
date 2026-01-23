# AGENTS.md - Notaría 4 Digital Core Rules

## 1. Architectural Constraints
- **Backend:** Python 3.11 on Cloud Run.
- **Frontend:** React on Firebase Hosting.
- **Database:** Firestore. Root collections: `clients`, `expedientes`, `facturas`.
- **Security:**
    - CSD Keys (.key) and Passwords MUST NEVER be stored in the codebase or Docker image.
    - Use **Google Secret Manager** to load credentials into memory at runtime.
- **OCR/NLP:**
    - Use `PyMuPDF` (fitz) for digital PDFs (Fast path).
    - Use `Tesseract` for scanned PDFs (Fallback).
    - Use `spaCy` for entity extraction.

## 2. Fiscal Validation Rules (CRITICAL)
- **CFDI 4.0 Name Validation:**
    - The `Nombre` attribute must match the SAT record exactly.
    - **Rule:** You MUST remove the corporate regime (e.g., "S.A. DE C.V.", "S.C.") using Regex before validation/signing.
    - Example: "INMOBILIARIA DEL PACÍFICO, S.A. DE C.V." -> "INMOBILIARIA DEL PACIFICO".
- **Zip Code:** Validate `DomicilioFiscalReceptor` against `c_CodigoPostal`.
- **ObjectImp (Objeto de Impuesto):**
    - Honorarios Notariales: `02` (Sí objeto).
    - Suplidos/Gastos (e.g., Registro Público): `01` (No objeto) OR use `ACuentaTerceros` node.

## 3. Specific Calculation Logic
- **Personas Morales Retentions:**
    - Trigger: If RFC length is 12 characters.
    - ISR Retention: 10% of base.
    - IVA Retention: 10.6667% (Two thirds of 16%).
    - Precision: Use `decimal.Decimal` with extended precision to avoid off-by-one cent errors.
- **ISAI Manzanillo (Local Tax):**
    - Formula: `ISAI = Max(PrecioOperacion, ValorCatastral) * TasaManzanillo`.
    - `TasaManzanillo` should be fetched from configuration (default 3%).
- **Copropiedad:**
    - The sum of percentages in `DatosAdquirientesCopSC` MUST be exactly `100.00%`.

## 4. Operational
- **Do not** use third-party APIs for core logic (TotalNot independence).
- **Do not** append new dependencies without checking `requirements.txt`.

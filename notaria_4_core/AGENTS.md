# Notaría 4 Digital Core - AGENTS.md

This directory contains the source code for the "Notaría 4 Digital Core" platform. All changes within this directory must adhere to the following architectural and fiscal constraints.

## 1. Architectural Principles (Serverless Sovereign)
- **Infrastructure:** Hybrid architecture using **Google Cloud Run** for heavy processing (Python/OCR) and **Firebase Cloud Functions** for event triggers.
- **Data Sovereignty:** All data, XMLs, and private keys reside in the Notary's GCP project. No reliance on third-party SaaS APIs for core logic.
- **Security:**
    - Private Keys (.key) and CSD Passwords must NEVER be stored in the codebase or docker images. Use **Google Secret Manager**.
    - Cloud Run services must access secrets only at runtime via memory.

## 2. Technology Stack & Versions
- **Backend Runtime:** Python 3.11 (slim)
- **Frontend:** React + Vite + TypeScript (hosted on Firebase Hosting)
- **Critical Libraries (Pinned Versions):**
    - `satcfdi==4.0.0` (Strict requirement for CFDI 4.0)
    - `spacy==3.7.4` (For NLP entity extraction)
    - `fastapi==0.109.2`
    - `pymupdf` (fitz) for digital PDF extraction
    - `pytesseract` for OCR fallback
    - `weasyprint` for PDF generation

## 3. Fiscal Rules & Business Logic (Strict)
### CFDI 4.0 Validation
- **Name Sanitization:** When reading "Razón Social" from a deed, you MUST remove the corporate regime (e.g., "S.A. DE C.V.", "S.C.") using Regex before sending to the PAC.
    - *Example:* "INMOBILIARIA DEL PACÍFICO, S.A. DE C.V." -> "INMOBILIARIA DEL PACIFICO"
    - The match must be exact with the SAT database (CSF).
- **Zip Code Validation:** Validate `DomicilioFiscalReceptor` against the local SAT catalog (`c_CodigoPostal`).

### Retentions (Personas Morales)
- **Trigger:** If `len(RFC_Receptor) == 12`.
- **ISR:** 10% retention on the base amount.
- **IVA:** Retention of two-thirds (2/3) of the transferred IVA.
    - *Formula:* `IVA_Trasladado * (2/3)` or approx `10.6667%`.
    - Use `decimal.Decimal` with high precision (prec=28) to avoid rounding errors.

### ISAI Manzanillo
- **Formula:** `Max(Precio_Operacion, Valor_Catastral) * Tasa_ISAI`.
- `Tasa_ISAI` should be fetched from configuration (e.g., Firebase Remote Config), defaulting to current year's rate (e.g., 3%).

### Copropiedad (Co-ownership)
- **Validation:** The sum of percentages in `DatosAdquirientesCopSC` MUST equal exactly `100.00%`.
- If the sum is `99.9%` or `100.1%`, the system must raise a blocking error.

## 4. Operational Guidelines
- **PDF Generation:** Use a "Hybrid" approach. Generate the Fiscal XML first using `satcfdi`, then render a PDF that includes both the fiscal data AND a non-fiscal section for "Other Expenses" (Suplidos) like rights or ISAI payments.
- **Testing:** All fiscal logic (taxes, retentions) must be unit tested with `unittest` or `pytest` before deployment.

# AGENTS.md - Notaría 4 Digital Core

This file defines the architectural and fiscal constraints for the "Notaría 4 Digital Core" project. All changes must strictly adhere to these rules.

## 1. Architectural Constraints
*   **Hybrid "Serverless Sovereign":**
    *   **Frontend:** React (SPA) on Firebase Hosting.
    *   **Backend:** Google Cloud Run (Python 3.11+) for heavy processing (OCR, XML Signing) and Firebase Cloud Functions (Node/Python) for event triggers.
    *   **Database:** Cloud Firestore. Root collections: `clients`, `expedientes`, `facturas`.
*   **Security:**
    *   **Secret Management:** Private keys (`.key`) and CSD passwords MUST NEVER be stored in the codebase or on the container filesystem. They must be accessed at runtime via **Google Secret Manager** directly into memory.
    *   **Digital Lock:** Once a status is "Timbrado", the record in Firestore must be immutable.

## 2. Fiscal Logic & Validation (Strict)
*   **CFDI 4.0 Compliance:**
    *   **Name Sanitization:** The `Nombre` attribute for the Receptor must match the CSF exactly but **exclude** the corporate regime (e.g., "S.A. DE C.V."). Use Regex to strip these suffixes before XML generation.
    *   **Zip Codes:** `DomicilioFiscalReceptor` must be validated against the SAT catalog (`c_CodigoPostal`).
*   **Tax Calculations:**
    *   **Persona Moral Retentions:** If RFC length is 12:
        *   ISR Retention: 10% of Subtotal.
        *   IVA Retention: 2/3 of IVA (approx 10.6667%). Use high-precision decimal context (`decimal.getcontext().prec = 50`) to avoid rounding errors.
    *   **ISAI Manzanillo:**
        *   Formula: `Max(OperationPrice, CadastralValue) * Rate`.
        *   Rate is dynamic (fetched from Config/Firestore).
*   **ObjectImp Codes:**
    *   Honorarios: `02` (Sí objeto de impuesto).
    *   Suplidos/Gastos: `01` (No objeto de impuesto) OR use `ACuentaTerceros` node.
*   **Copropiedad (Co-ownership):**
    *   The sum of percentages in `DatosAdquirientesCopSC` MUST equal exactly **100.00%**. If `99.9%` or `100.1%`, the process must halt.

## 3. Technology Stack
*   **Python:** 3.11+
*   **XML/Fiscal:** `satcfdi` (latest stable).
*   **OCR:** `pytesseract` (Tesseract) + `pymupdf` (Fitz).
*   **NLP:** `spacy` (Spanish models).

## 4. Development
*   **Testing:** All fiscal logic must be unit tested (`pytest`) covering edge cases (rounding, name cleaning).
*   **Performance:** OCR tasks run in Cloud Run with high memory limits. Use `preload='none'` for large media assets in frontend.

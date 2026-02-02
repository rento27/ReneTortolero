# AGENTS.md - Notaría 4 Digital Core

## Project Scope
This directory (`notaria_4_core/`) contains the source code for the "Notaría 4 Digital Core" platform, a sovereign serverless architecture designed to handle fiscal operations (CFDI 4.0), document digitization (OCR/NLP), and secure storage for Notaría Pública No. 4 in Manzanillo, Colima.

## Architectural Constraints
1.  **Serverless Sovereign**: Logic runs on Google Cloud Run (Python) and Firebase Cloud Functions (Node.js/Python). Data resides in Firestore.
2.  **No Third-Party Dependencies**: Do not rely on external SaaS APIs for core logic (e.g., TotalNot).
3.  **Security**:
    *   Private Keys (.key) and CSD Passwords must **NEVER** be stored in the codebase or docker images.
    *   Use **Google Secret Manager** to load credentials directly into memory.

## Fiscal & Business Rules (Strict Enforcement)

### 1. CFDI 4.0 Validation
*   **Name Sanitization**: The `Receptor` name must match the SAT database exactly.
    *   **Rule**: Remove corporate regimes (e.g., "S.A. DE C.V.", "S.C.") using regex.
    *   **Rule**: Remove trailing punctuation and extra spaces.
    *   **Rule**: Convert to uppercase.
*   **Zip Code**: Verify `DomicilioFiscalReceptor` against the SAT `c_CodigoPostal` catalog.

### 2. Retention Logic (Persona Moral)
*   **Trigger**: If `len(RFC_Receptor) == 12` (Persona Moral).
*   **ISR Retention**: 10% of the taxable base (Subtotal).
*   **IVA Retention**: 10.666667% (Two-thirds of 16% IVA).
*   **Precision**: Calculations must use `decimal.Decimal` with high precision (set context to 50 places) to avoid rounding errors.

### 3. ISAI Manzanillo (Local Tax)
*   **Formula**: `ISAI = Max(PrecioOperacion, ValorCatastral) * TasaManzanillo`
*   **Rate**: Defaults to 3% (0.03), but should be fetched from configuration (Firebase Remote Config).

### 4. Copropiedad (Co-ownership)
*   **Validation**: When multiple acquirers exist (`DatosAdquirientesCopSC`), the sum of their percentages must equal **exactly 100.00%**.
*   **Action**: If sum != 100.00, the process must halt.

### 5. Concept Classification
*   **Honorarios**: `ObjetoImp` = "02" (With Taxes).
*   **Suplidos/Gastos**: `ObjetoImp` = "01" (No Tax) or use the `ACuentaTerceros` node.

## Technology Stack
*   **Backend**: Python 3.11 (FastAPI) on Cloud Run.
*   **Libraries**: `satcfdi` (XML), `spacy` (NLP), `pytesseract` (OCR).
*   **Database**: Cloud Firestore.

## Testing
*   All fiscal logic must be covered by unit tests in `backend/tests/`.
*   Ensure rounding precision is tested.

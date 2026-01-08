# AGENTS.md - Notaría 4 Digital Core

## Scope
This document governs the development of the "Notaría 4 Digital Core" project rooted in the `notaria_4_core` directory.

## Project Vision
A sovereign, serverless platform for Notaría Pública No. 4 (Manzanillo, Colima) to replace third-party SaaS ("TotalNot"). The system handles CFDI 4.0 invoicing, AI-based deed extraction, and local tax calculations.

## Architectural Constraints (The "Serverless Sovereign" Model)
1.  **Backend (Heavy Lifting):** Google Cloud Run running Python 3.11.
    -   Must use `satcfdi` for XML generation/signing.
    -   Must use `spacy` (NLP) and `tesseract` (OCR) for document processing.
    -   Secrets (CSD keys, passwords) must be accessed via **Google Secret Manager** in memory only.
2.  **Frontend:** React/Vue hosted on Firebase Hosting.
3.  **Database:** Google Cloud Firestore.
    -   Root Collections: `clientes`, `expedientes`, `facturas`.
    -   Catalogos: Large catalogs (Zip codes) stored in Storage/Sharded.
4.  **Events:** Cloud Functions (2nd Gen) for triggers (WhatsApp, File Uploads).

## Critical Business Logic (DO NOT VIOLATE)

### 1. CFDI 4.0 Strict Validation
-   **Name Sanitization:** Receiver name must match SAT records exactly but **EXCLUDE** the regime.
    -   *Rule:* Use Regex to strip "S.A. DE C.V.", "S.C.", etc., before sending to PAC.
-   **Zip Code:** Must cross-reference `c_CodigoPostal`. Verify State/Municipality matches the provided Zip.

### 2. Fiscal Engineering (The "Fiscal Rules Engine")
-   **Persona Moral Detection:** If RFC length is **12 characters**:
    -   **ISR Retention:** 10% of Subtotal.
    -   **IVA Retention:** Two-thirds (2/3) of IVA. **Math:** `IVA_Trasladado * (2/3)` or approx **10.6667%**.
    -   *Requirement:* Use high-precision decimal math (Python `decimal` module) to avoid off-by-one cent errors.
-   **ISAI Manzanillo (Local Tax):**
    -   Formula: `Max(Precio_Operacion, Valor_Catastral) * Tasa_ISAI`.
    -   Configuration: `Tasa_ISAI` must be fetched from **Firebase Remote Config** (not hardcoded).
-   **Non-Object Items:** "Suplidos" (reimbursements) must be `ObjetoImp="01"` or use `ACuentaTerceros`.

### 3. Complemento de Notarios
-   **Constants:** `NumNotaria: 4`, `EntidadFederativa: 06` (Colima).
-   **Copropiedad:** The sum of `Porcentaje` in `DatosAdquirientesCopSC` must strictly equal **100.00%**.

### 4. AI/OCR Pipeline
-   **Strategy:** "Digital First, Scan Fallback".
    1.  Attempt extraction with `PyMuPDF` (fitz).
    2.  If text density low, fallback to `Tesseract` (OCR).
    3.  NLP: Use `spacy` to identify Entities (Buyer, Seller, Property, Price).

## Operational Guidelines
-   **Output:** Hybrid PDFs. Fiscal page (from XML) + Administrative page ("Cuenta de Gastos").
-   **Security:** `expedientes` cannot be modified if `status == 'Timbrado'`.

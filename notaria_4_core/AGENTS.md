# AGENTS.md - Notaría 4 Digital Core Rules

This file documents the strict architectural and fiscal constraints for the "Notaría 4 Digital Core" project. All code must adhere to these rules.

## 1. Fiscal Rules (CFDI 4.0)

### 1.1 Name Sanitization
*   **Rule:** The `Receptor.Nombre` must match the SAT records EXACTLY but MUST NOT include the corporate regime.
*   **Implementation:** Use Regex to strip suffixes like "S.A. DE C.V.", "S.C.", "S.A.P.I. DE C.V.", etc.
*   **Example:** "INMOBILIARIA DEL PACÍFICO, S.A. DE C.V." -> "INMOBILIARIA DEL PACÍFICO".

### 1.2 Zip Code Validation
*   **Rule:** `DomicilioFiscalReceptor` must be validated against the `c_CodigoPostal` catalog.
*   **Check:** Verify that the provided Zip Code corresponds to the State and Municipality of the client.

### 1.3 ObjectImp (Objeto de Impuesto)
*   **Honorarios (Fees):** Must use code `02` (Sí objeto de impuesto).
*   **Suplidos/Gastos (Expenses):** Must use code `01` (No objeto de impuesto) OR be handled via the `ACuentaTerceros` node.

### 1.4 Persona Moral Retentions
*   **Trigger:** If Receiver RFC length is 12 (Persona Moral).
*   **ISR Retention:** 10% of Subtotal.
*   **IVA Retention:** Two-thirds (2/3) of the transferred IVA.
    *   **Math:** `Subtotal * 0.16 * (2/3)` or approx `10.6667%`.
    *   **Precision:** Use `decimal.Decimal` with high precision context to avoid off-by-one cent errors.

## 2. Local Law (Manzanillo, Colima)

### 2.1 ISAI Calculation
*   **Formula:** `ISAI = Max(OperationPrice, CatastralValue) * TasaManzanillo`.
*   **Rate:** The rate (e.g., 3%) should be fetched from configuration (Firebase Remote Config), not hardcoded permanently.

## 3. Complemento de Notarios

### 3.1 Hardcoded Values
*   `NumNotaria`: 4
*   `EntidadFederativa`: 06 (Colima)
*   `Adscripcion`: MANZANILLO COLIMA

### 3.2 Copropiedad (Co-ownership)
*   **Validation:** The sum of percentages in `DatosAdquirientesCopSC` must be EXACTLY `100.00%`.
*   **Action:** If sum != 100.00, raise an error (do not round silently).

## 4. Architecture

### 4.1 Secrets
*   **Rule:** NEVER store `.key` files or passwords in the code or Docker image.
*   **Implementation:** Use `google-cloud-secret-manager` to load credentials directly into memory.

### 4.2 Database
*   **Constraint:** Do not update `expedientes` or `facturas` once their status is "Timbrado".

### 4.3 Libraries
*   **Python:** Use `satcfdi` for XML. Use `pymupdf` (fitz) + `tesseract` for OCR. Use `spacy` for NLP.

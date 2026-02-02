# Notaría 4 Digital Core - AGENTS.md

This directory contains the source code for the "Notaría 4 Digital Core" platform. All changes must adhere to the following architectural and fiscal constraints.

## 1. Architectural Constraints
*   **Architecture:** Serverless Sovereign (Firebase + Google Cloud Run).
*   **Backend Runtime:** Python 3.11 (strictly enforced via Docker).
*   **Infrastructure:**
    *   **Cloud Run:** For heavy processing (OCR, XML Signing, Fiscal Logic).
    *   **Firebase Functions (2nd Gen):** For event triggers only.
    *   **Firestore:** NoSQL database using Root Collections (clients, expedientes, facturas).
    *   **Secret Manager:** All cryptographic keys (CSD, Private Keys) must be loaded from Google Secret Manager. **NEVER** store keys in the codebase or Docker image.

## 2. Fiscal Engineering & Logic (Strict)
*   **Library Standard:** Use `satcfdi` (Python) for all CFDI 4.0 generation and signing.
*   **Decimal Precision:** Use `decimal` library with high precision context. Avoid floating point errors.
*   **ISAI Manzanillo Rule:**
    *   `ISAI = Max(Precio_Operacion, Valor_Catastral) * Tasa_Manzanillo`
    *   Default Tasa: 3% (0.03).
*   **Persona Moral Retentions (RFC length == 12):**
    *   **ISR:** 10% of Subtotal.
    *   **IVA:** 10.6667% (Two-thirds of 16% IVA) of Subtotal.
    *   *Note:* Do not round intermediate calculations until the final result requires it for XML.
*   **Name Sanitization:**
    *   Corporate Regimes (e.g., "S.A. DE C.V.", "S.C.") **MUST** be removed from the `Nombre` attribute of the Receptor node to comply with CFDI 4.0 matching rules.
    *   Use Regex for strict removal.
*   **Copropiedad Validation:**
    *   The sum of percentages in `DatosAdquirientesCopSC` **MUST** equal exactly `100.00%`.
*   **ObjetoImp:**
    *   Honorarios: `02` (Si objeto de impuesto).
    *   Suplidos/Gastos: `01` (No objeto) OR use `ACuentaTerceros` node.

## 3. Operational Guidelines
*   **OCR:** Use `pytesseract` as fallback for scanned documents, `pymupdf` (fitz) for digital natives.
*   **Testing:** All fiscal logic must be unit tested before submission.

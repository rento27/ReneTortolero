# AGENTS.md - Notaría 4 Digital Core

This document defines the architectural and fiscal constraints for the Notaría 4 Digital Core project. All changes must adhere to these rules.

## 1. Fiscal Strictness (The "Digital Constitution")

### A. CFDI 4.0 Validation
*   **Names:** Must be exact to the SAT Constancia but **MUST NOT** include the Regime Societario (e.g., "S.A. DE C.V."). Use `fiscal_engine.sanitize_name`.
*   **Zip Codes:** Strict cross-validation required. Verify `c_CodigoPostal` matches the state/municipality of the client.
*   **ObjectImp:**
    *   Honorarios: `02` (Sí objeto).
    *   Suplidos: `01` (No objeto) or use `ACuentaTerceros`.

### B. Retentions (Persona Moral)
*   **Trigger:** If Receiver RFC length is **12**.
*   **ISR:** 10% of Subtotal.
*   **IVA:** 2/3 of the VAT (10.6667%).
*   **Precision:** Use `decimal.Decimal` with high precision context. Do not use float.

### C. Local Taxes (Manzanillo)
*   **ISAI Formula:** `Max(OperationPrice, CadastralValue) * Rate`.
*   **Rate:** Controlled via Firebase Remote Config (default ~3% for 2025).

### D. Complemento de Notarios
*   **Notary Num:** 4
*   **State:** 06 (Colima)
*   **Copropiedad:** The sum of percentages (`DatosAdquirientesCopSC`) must be exactly **100.00%**.

## 2. Architecture Constraints

### A. Serverless Sovereign
*   **Secrets:** Never commit `.key` or `.cer` files. Use Google Secret Manager and load in-memory via `signer.py`.
*   **Database:** Cloud Firestore. Root collections: `clients`, `expedientes`, `facturas`.
*   **Locking:** Documents in `expedientes` must be READ-ONLY if status is "Timbrado".

### B. Tech Stack
*   **Backend:** Python 3.11+ on Cloud Run (FastAPI).
*   **Frontend:** React (Vite) on Firebase Hosting.
*   **OCR:** PyMuPDF (First pass) -> Tesseract (Fallback).
*   **XML:** `satcfdi` library (Pinned version 4.0.0).

## 3. Developer Guidelines
*   **Do not** introduce heavy frameworks (Django, etc.). Keep it lightweight FastAPI.
*   **Test** fiscal logic with `pytest` before deploying. Math errors are legal risks here.

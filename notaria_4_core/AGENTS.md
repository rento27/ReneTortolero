# Notaría 4 Digital Core - AGENTS.md

This directory contains the "Notaría 4 Digital Core" system. All changes here must adhere to the "Serverless Sovereign" architecture.

## Architectural Constraints

1.  **Backend:** Python 3.11+ on Google Cloud Run.
    *   Use `fastapi` for the API.
    *   Use `satcfdi` for all CFDI 4.0 operations.
    *   **Secrets:** NEVER hardcode keys. Use `google-cloud-secret-manager`.
    *   **Logic:** Business logic resides in `backend/lib/`.

2.  **Frontend:** React (Vite) + TypeScript on Firebase Hosting.
    *   State management must handle "Human-in-the-Loop" verification.

3.  **Database:** Cloud Firestore.
    *   No monolithic documents. Use root collections: `clients`, `expedientes`, `facturas`.

## Fiscal & Operational Rules (NON-NEGOTIABLE)

1.  **CFDI 4.0 Strictness:**
    *   **Names:** Must be sanitized against SAT records (remove "S.A. DE C.V.", "S.C.", etc.) using Regex.
    *   **Zip Codes:** Must be validated against `c_CodigoPostal` before XML generation.

2.  **Tax Logic:**
    *   **Persona Moral:** If RFC length is 12:
        *   ISR Retention: 10%
        *   IVA Retention: 10.6667% (Two-thirds of 16%).
    *   **ISAI (Manzanillo):** `Max(OperationPrice, CadastralValue) * Tasa`.
        *   `Tasa` must be fetched from configuration (e.g., Firebase Remote Config), defaulting to 0.03 (3%).

3.  **Accuracy:**
    *   **Copropiedad:** The sum of percentages in `DatosAdquirientesCopSC` MUST equal exactly 100.00%.
    *   **Decimal Precision:** Use `decimal.Decimal` with ample precision (context prec=28) for all currency calculations.

4.  **Security:**
    *   **NOM-151:** Internal receipts ("Cuenta de Gastos") must be prepared for timestamping.
    *   **Digital Lock:** Once a deed is "Timbrado", it is immutable.

## Deployment
*   The backend is containerized. Check `backend/Dockerfile` for system dependencies (Tesseract, etc.).

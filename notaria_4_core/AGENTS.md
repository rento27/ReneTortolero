# AGENTS.md - Notaría 4 Digital Core

## Project Scope
This directory (`notaria_4_core/`) contains the source code for the "Notaría 4 Digital Core" platform. This is a Sovereign Serverless system running on Google Cloud Platform (Cloud Run + Firebase).

## Architectural Constraints (Strict)
1.  **Backend:** Must use **Python 3.11** with **FastAPI** running on **Cloud Run**.
    *   Reasons: Requires `satcfdi` (XML signing), `tesseract-ocr` (system dependency), and `spacy` (heavy memory).
2.  **Database:** Cloud Firestore.
    *   **Rule:** Use Root Collections (`clients`, `expedientes`, `facturas`). Avoid deep nesting.
    *   **Sharding:** Large catalogs (like `c_CodigoPostal`) must be sharded or stored as JSON in Storage.
3.  **Security:**
    *   **Secret Manager:** Private keys (`.key`) and CSD passwords MUST be accessed via Google Secret Manager. **NEVER** write these to disk or store in the codebase.
4.  **Frontend:** React (Vite) + Firebase Hosting.

## Fiscal Logic (Non-Negotiable)
1.  **Name Sanitization:**
    *   For CFDI 4.0, the `Nombre` attribute must NOT contain the regime (e.g., "S.A. DE C.V.").
    *   **Action:** Implement regex cleaning to strip these suffixes before stamping.
2.  **Persona Moral Retentions:**
    *   If `Len(RFC_Receptor) == 12`:
        *   ISR Retention: 10%
        *   IVA Retention: 10.6667% (2/3 of VAT).
3.  **ISAI Manzanillo:**
    *   Formula: `Max(PrecioOperacion, ValorCatastral) * TasaManzanillo`.
4.  **Copropiedad:**
    *   Sum of percentages in `DatosAdquirientesCopSC` MUST equal exactly `100.00%`.

## Operational
*   **Dependencies:** Do not add new system dependencies to the Dockerfile without verifying Cloud Run compatibility.
*   **Testing:** All fiscal calculations must use `decimal` precision, never `float`.

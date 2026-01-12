# AGENTS.md - Notaría 4 Digital Core

## Project Scope
This directory (`notaria_4_core`) contains the implementation of the sovereign notary management system for Notaría Pública No. 4 Manzanillo.

## Architecture: "Serverless Sovereign"
*   **Infrastructure:** Google Cloud Platform (GCP) + Firebase.
*   **Backend:** Cloud Run (Python 3.11). Handles heavy processing: OCR, NLP, CFDI Signing.
*   **Frontend:** React (Vite) hosted on Firebase Hosting.
*   **Database:** Firestore (NoSQL).
*   **Secrets:** Google Secret Manager (Strictly no keys in code).

## Critical Fiscal & Business Constraints
**WARNING: These rules are legally binding. Do not modify without explicit instruction.**

1.  **CFDI 4.0 Name Sanitization:**
    *   Receiver Names must match SAT records exactly but **MUST NOT** include the regime.
    *   *Action:* Use Regex to strip "S.A. DE C.V.", "S.C.", etc., from the end of the name string before generating XML.

2.  **Persona Moral Retentions (RFC Len = 12):**
    *   If RFC length is 12 characters, apply strict retentions:
        *   **ISR:** 10%
        *   **IVA:** 10.6667% (Two-thirds of 16%).
    *   *Precision:* Use `decimal` library with high precision context. Do not use float.

3.  **ISAI Manzanillo Algorithm:**
    *   Formula: `Max(OperationPrice, CatastralValue) * Tasa`.
    *   `Tasa` is fetched from **Firebase Remote Config** (default ~3% but variable per year).

4.  **Complemento Notarios:**
    *   `NumNotaria`: 4
    *   `EntidadFederativa`: 06 (Colima)
    *   `DatosAdquirientesCopSC`: The sum of percentages (`Porcentaje`) must equal **100.00%** exactly. Throw validation error if sum is 99.99% or 100.01%.

5.  **Security:**
    *   Never commit `.key`, `.cer`, or `.pfx` files.
    *   Use `google-cloud-secret-manager` to load credentials into memory at runtime.

6.  **Directory Structure:**
    *   `backend/`: Python FastAPI app (Cloud Run).
    *   `frontend/`: React application.
    *   `firebase/`: Cloud Functions and Rules.

## Dependencies (Backend)
*   `python:3.11-slim`
*   `satcfdi` (CFDI 4.0 & Signing)
*   `spacy` (NLP) + `es_core_news_lg`
*   `pymupdf` (PDF Parsing)
*   `pytesseract` (OCR fallback)
*   `weasyprint` (PDF Report Gen)

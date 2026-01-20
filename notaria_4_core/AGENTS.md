# Notaría 4 Digital Core - AGENTS.md

## 1. Architecture & Strategy
*   **Model:** Serverless Sovereign (Google Cloud Platform).
*   **Frontend:** React (Vite) + Firebase Hosting.
*   **Backend:** Hybrid.
    *   **Cloud Run (Heavy):** Python 3.11 + FastAPI. Handles OCR (Tesseract), PDF Parsing (PyMuPDF), NLP (spaCy), and XML Signing (satcfdi).
    *   **Cloud Functions (Light):** Node.js/Python 2nd Gen. Handles Event Triggers (Firestore/Storage events).
*   **Database:** Cloud Firestore (Root collections: `clientes`, `expedientes`, `facturas`).
*   **Security:** Private keys (.key) and passwords MUST be loaded from **Google Secret Manager** directly into memory. NEVER write sensitive files to disk.

## 2. Fiscal Engineering & Logic (STRICT)
*   **CFDI 4.0 Compliance:**
    *   **Name Sanitization:** REMOVE corporate regime (e.g., "S.A. DE C.V.") from Receiver Name before stamping. Must match SAT database exactly (uppercase, no regime).
    *   **ZIP Code:** Validate `DomicilioFiscalReceptor` against local SAT catalog (`c_CodigoPostal`).
    *   **ObjectImp:**
        *   Honorarios -> `02` (Sí objeto de impuesto).
        *   Suplidos/Gastos -> `01` (No objeto) OR use `ACuentaTerceros` node.
*   **Persona Moral Rules (RFC length = 12):**
    *   **ISR Retention:** 10% of base.
    *   **IVA Retention:** 2/3 of IVA transferred (10.6667%).
    *   **Precision:** Use `decimal` library with extended context.
*   **ISAI Manzanillo (Local Tax):**
    *   Formula: `Max(Operacion_Monto, Valor_Catastral) * Tasa_Manzanillo`.
    *   `Tasa_Manzanillo` defaults to 3% (configurable via Firebase Remote Config).
*   **Copropiedad:**
    *   Sum of percentages in `DatosAdquirientesCopSC` MUST equal **100.00%** exactly. Throw error if 99.9% or 100.1%.

## 3. OCR & NLP Pipeline (Cloud Run)
1.  **Fast Layer:** Try `fitz` (PyMuPDF) for digital-native text.
2.  **Deep Layer:** Fallback to `pytesseract` for scanned images.
3.  **NLP:** Use `spaCy` (custom model `ner_notaria`) to extract:
    *   VENDEDOR / ADQUIRENTE names.
    *   INMUEBLE address.
    *   MONTO operation.
4.  **Verification:** Implementation of "Human-in-the-Loop" UI is mandatory.

## 4. Operational Constraints
*   **Dependencies:** `satcfdi` (XML), `spacy` (NLP), `pytesseract` (OCR), `pymupdf` (PDF), `fastapi` (API).
*   **Docker:** Base image `python:3.11-slim`. Install system deps: `tesseract-ocr`, `libgl1`, `libxml2`, `libxslt-dev`.
*   **NOM-151:** Internal receipts must be stamped for data integrity (Future Phase).

## 5. Directory Structure
*   `backend/`: Python Cloud Run service.
*   `frontend/`: React application.
*   `firestore.rules`: Security rules.

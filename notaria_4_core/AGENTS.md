# AGENTS.md - Notaría 4 Digital Core

This file defines the strict architectural and fiscal constraints for the "Notaría 4 Digital Core" project. All changes must adhere to these rules.

## 1. Architectural Principles

*   **Serverless Sovereign:** The system must run on Google Cloud Platform (GCP) using a hybrid approach:
    *   **Cloud Run:** For heavy processing (Python 3.11, OCR, XML Signing).
    *   **Firebase Cloud Functions (2nd Gen):** For event-driven tasks (WhatsApp notifications, storage triggers).
    *   **Firestore:** Primary NoSQL database.
*   **Security First:**
    *   **NO CSD Keys on Disk:** `.key` files and passwords must NEVER be stored in the source code or the container file system. They must be loaded directly into memory from **Google Secret Manager**.
    *   **Digital Lock:** Once an `expediente` or `factura` status is "Timbrado", it must be immutable.
*   **Containerization:** The backend must be Dockerized using `python:3.11-slim` and include necessary system dependencies (`tesseract-ocr`, `libgl1`, etc.).

## 2. Fiscal Logic & Validation (CRITICAL)

### CFDI 4.0 Compliance
*   **Name Sanitization:** The `Receptor` name in the XML must match the SAT database exactly.
    *   **Rule:** You MUST remove the corporate regime (e.g., " S.A. DE C.V.", " S.C.") using strict Regex validation.
    *   *Example:* "INMOBILIARIA DEL PACÍFICO, S.A. DE C.V." -> "INMOBILIARIA DEL PACIFICO".
*   **Zip Code Validation:** Validate `DomicilioFiscalReceptor` against the `c_CodigoPostal` catalog. Cross-reference with the State code.
*   **ObjetoImp:**
    *   **02 (Sí objeto de impuesto):** For Honorarios Notariales.
    *   **01 (No objeto de impuesto):** For Suplidos/Gastos (unless using `ACuentaTerceros` node).

### Retention Rules (Personas Morales)
*   **Trigger:** If `Len(RFC_Receptor) == 12`.
*   **ISR:** 10% retention on the base amount.
*   **IVA:** Two-thirds (2/3) retention of the IVA amount (approx 10.6667%).
*   **Precision:** Calculations must use high-precision decimals (at least 6 places) before rounding to 2 places for the XML to avoid "off-by-one cent" errors.

### ISAI Manzanillo (Local Tax)
*   **Formula:** `ISAI = Max(PrecioOperacion, ValorCatastral) * Tasa_Manzanillo`.
*   **Configuration:** `Tasa_Manzanillo` must be fetched from Firebase Remote Config (default 3%).

### Copropiedad (Co-ownership)
*   **Validation:** The sum of percentages in `DatosAdquirientesCopSC` MUST equal exactly `100.00%`.
*   **Action:** If the sum deviates (e.g., 99.99%), the process must halt and request manual verification.

## 3. Technology Stack

*   **Backend:** Python 3.11, FastAPI, `satcfdi` (v4.0.0+), `spacy`, `pytesseract`, `pymupdf`.
*   **Frontend:** React, Vite, TypeScript, Tailwind CSS.
*   **Database:** Firestore.

## 4. Operational Constraints

*   **Human-in-the-Loop:** Critical extraction data (Amounts, Names) must be verified by a human via a UI that shows the PDF and extracted data side-by-side.
*   **Testing:** All fiscal logic must be covered by unit tests in `backend/test_fiscal.py`.

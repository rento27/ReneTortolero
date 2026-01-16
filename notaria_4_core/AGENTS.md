# AGENTS.md - Notaría 4 Digital Core

This file outlines the architectural constraints, coding standards, and operational guidelines for the "Notaría 4 Digital Core" project.

**Scope:** Entire `notaria_4_core/` directory.

## 1. Project Philosophy
*   **Sovereignty:** Dependencies on external SaaS (like TotalNot) are prohibited. All core logic must be owned and run on our infrastructure (GCP/Firebase).
*   **Serverless First:** Prioritize Firebase Cloud Functions and Cloud Run. Avoid persistent VMs.
*   **Human-in-the-Loop:** AI suggestions must always be verifiable by a human operator via the UI.
*   **Strict Fiscal Compliance:** No approximations. Fiscal calculations must be mathematically exact (Decimal precision) and legally compliant with SAT CFDI 4.0.

## 2. Technology Stack & Constraints

### Backend (Cloud Run)
*   **Language:** Python 3.11+
*   **Framework:** FastAPI
*   **Key Libraries:**
    *   `satcfdi` (v4.0.0+) for XML generation/signing.
    *   `spacy` for NLP.
    *   `pymupdf` (fitz) & `pytesseract` for OCR.
*   **Docker:** Must use `python:3.11-slim` base. Explicitly install system deps: `tesseract-ocr`, `libgl1`.
*   **Security:** NEVER commit `.key`, `.cer`, or passwords. Use Google Secret Manager.

### Frontend
*   **Framework:** React (Vite) + TypeScript.
*   **Hosting:** Firebase Hosting.
*   **Styling:** Tailwind CSS.
*   **State:** Context API or simple state management (avoid Redux unless necessary).

### Database (Firestore)
*   **Root Collections:** `clients`, `expedientes`, `facturas`.
*   **Validation:** Use Firestore Security Rules to lock `expedientes` and `facturas` once status is "Timbrado".

## 3. Critical Business Rules (DO NOT BREAK)

### CFDI 4.0
*   **Names:** Must be uppercase. Remove regime (e.g., "S.A. DE C.V.") via Regex before sending to PAC.
*   **Zip Codes:** Validate against `c_CodigoPostal`.
*   **Payment:** "Suplidos" must be `ObjetoImp: 01` or `ACuentaTerceros`.

### Fiscal Logic
*   **Persona Moral:**
    *   Trigger: `len(RFC) == 12`.
    *   ISR Retention: 10%.
    *   IVA Retention: 10.6667% (Two-thirds).
*   **ISAI Manzanillo:**
    *   Formula: `Max(PrecioOperacion, ValorCatastral) * Tasa`.
    *   `Tasa` must be fetched from configuration (default 3%).
*   **Copropiedad:** Sum of percentages in `DatosAdquirientesCopSC` must be exactly 100.00%.

## 4. Coding Standards
*   **Python:** Follow PEP 8. Use `decimal.Decimal` for ALL monetary calculations.
*   **Comments:** Explain *why*, not just *what*, especially in fiscal formulas.
*   **Testing:** Critical fiscal functions (retentions, ISAI) MUST have unit tests covering edge cases.

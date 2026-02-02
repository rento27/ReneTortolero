# Notaría 4 Digital Core - AGENTS.md

This file defines the architectural, fiscal, and operational constraints for the "Notaría 4 Digital Core" project. All changes within this directory must adhere to these rules.

## 1. Architectural Principles ("Serverless Sovereign")
*   **Infrastructure:** strictly Google Cloud Platform (GCP) + Firebase.
*   **Compute:**
    *   **Heavy Lifting (OCR, NLP, XML Signing):** Must run on **Cloud Run** (Python 3.11+).
    *   **Eventing/Triggers:** Must use **Cloud Functions (2nd Gen)**.
*   **Database:** **Cloud Firestore** (NoSQL).
    *   Root Collections: `clients`, `expedientes`, `facturas`.
    *   **Strict Rule:** No subcollections deeper than 1 level unless absolutely necessary for atomicity.
*   **Security:**
    *   **Secrets:** NEVER commit `.key`, `.cer`, or passwords. Use **Google Secret Manager**.
    *   **Immutability:** `facturas` and `expedientes` must be locked (read-only) once status is "Timbrado".

## 2. Fiscal Engineering (Non-Negotiable)
*   **CFDI 4.0 Strictness:**
    *   **Names:** Must be sanitized (Regex) to remove regimes (e.g., "S.A. DE C.V.") before sending to PAC.
    *   **Zip Codes:** Must be validated against SAT catalog `c_CodigoPostal`.
*   **Persona Moral Logic:**
    *   Trigger: If `len(RFC) == 12`.
    *   **ISR Retention:** 10%.
    *   **IVA Retention:** 10.6667% (Two-thirds). **Must use high-precision decimal context.**
*   **ISAI Manzanillo:**
    *   Algorithm: `Max(Price, CatastralValue) * Tasa`.
    *   `Tasa` must be fetched from Firebase Remote Config (default ~3%).
*   **Complemento Notarios:**
    *   `NumNotaria`: 4
    *   `Entidad`: 06 (Colima)
    *   `Copropiedad`: Sum of percentages must equal **exactly 100.00%**.

## 3. Technology Stack
*   **Backend:** Python 3.11 (FastAPI).
    *   **XML:** `satcfdi` (v4.0.0+).
    *   **OCR:** `pytesseract` (with system `tesseract-ocr`), `pymupdf` (fitz).
    *   **NLP:** `spacy`.
*   **Frontend:** React (Vite) + TypeScript.
    *   Hosting: Firebase Hosting.

## 4. Coding Standards
*   **Python:** Type hints (PEP 484) required. Use `decimal.Decimal` for ALL monetary values.
*   **Comments:** Explain the *why*, especially for fiscal logic (e.g., "Retention rule per LIVA Art 3").

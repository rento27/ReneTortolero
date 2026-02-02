# AGENTS.md - Notaría 4 Digital Core

This file documents the architectural constraints, business rules, and technical strategy for the "Notaría 4 Digital Core" project. All changes must adhere to these directives.

## 1. Project Overview
"Notaría 4 Digital Core" is a proprietary SaaS built on **Google Firebase** and **Google Cloud Platform (GCP)** to replace third-party solutions. It prioritizes technological sovereignty, fiscal precision (CFDI 4.0), and automation.

## 2. Technical Architecture ("Serverless Sovereign")
- **Frontend:** React/Vue.js Single Page Application (SPA) hosted on **Firebase Hosting**.
- **Backend:** Hybrid Architecture.
    - **Cloud Run:** Python 3.11 container for heavy processing (OCR, XML Signing, `satcfdi`).
    - **Cloud Functions (2nd Gen):** Event-driven triggers (Node.js/Python).
- **Database:** **Cloud Firestore** (NoSQL).
- **Security:** **Google Secret Manager** for CSD (Digital Seal Certificate) keys. Keys must *never* be stored in code or disk.

## 3. Fiscal Rules (Strict Compliance)
### 3.1 CFDI 4.0 Validation
- **Name Sanitization:** Must remove corporate regimes (e.g., "S.A. DE C.V.") via Regex before sending to PAC. Match exact SAT database name.
- **Postal Code:** Validate `DomicilioFiscalReceptor` against SAT catalogs (`c_CodigoPostal`).
- **ObjectImp (Tax Object):**
    - **Honorarios:** Code `02` (Sí objeto de impuesto).
    - **Suplidos/Gastos:** Code `01` (No objeto) OR use `ACuentaTerceros` node.

### 3.2 Persona Moral (Corporate) Retentions
- **Trigger:** If RFC length is 12 characters.
- **ISR:** 10% retention.
- **IVA:** Two-thirds (2/3) retention (approx 10.6667%).
- **Precision:** Use `decimal` library with high precision context to avoid off-by-one errors.

### 3.3 ISAI Manzanillo (Local Tax)
- **Formula:** `Max(PrecioOperacion, ValorCatastral) * Tasa_Manzanillo`.
- **Tasa:** Configurable via **Firebase Remote Config** (default ~3%).

## 4. Notary Complement (Complemento de Notarios)
- **Data Integrity:** Sum of percentages in `DatosAdquirientesCopSC` must equal exactly `100.00%`.
- **Fields:**
    - `NumNotaria`: 4
    - `EntidadFederativa`: 06 (Colima)
    - `Adscripcion`: MANZANILLO COLIMA

## 5. Automation & Intelligence
- **OCR Strategy:**
    1. **PyMuPDF (`fitz`):** Fast path for digital PDFs.
    2. **Tesseract:** Fallback for scanned documents.
- **NLP:** Use **spaCy** for entity extraction (Vendedor, Adquirente, Inmueble, Monto).
- **Human-in-the-Loop:** UI must show PDF side-by-side with extracted data for verification.

## 6. Development Guidelines
- **Language:** Python 3.11 for Backend Core.
- **Libraries:** `satcfdi` (XML/Signing), `fastapi`, `spacy`, `pytesseract`.
- **Environment:** Do not hardcode secrets. Use Secret Manager.

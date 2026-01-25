# AGENTS.md - Notaría 4 Digital Core

This file outlines the strict architectural and fiscal constraints for the "Notaría 4 Digital Core" project. All code and modifications must adhere to these rules.

## 1. Architectural Principles: "Serverless Sovereign"
*   **Infrastructure**: The system runs on **Google Cloud Platform** (Project owned by Notaría 4).
*   **Backend**:
    *   **Cloud Run (Python 3.11)**: Handles heavy processing: OCR (Tesseract), NLP (spaCy), and XML Signing (satcfdi).
    *   **Firebase Cloud Functions**: Handles lightweight event-driven triggers (WhatsApp notifications, etc.).
*   **Database**: **Cloud Firestore** (NoSQL).
*   **Secrets**: Private keys (.key) and passwords MUST be loaded from **Google Secret Manager** at runtime. NEVER commit them to git or include them in Docker images.

## 2. Fiscal Logic & Validation Rules (CRITICAL)
*   **CFDI 4.0 Compliance**:
    *   **Name Sanitization**: Remove Corporate Regimes (e.g., "S.A. DE C.V.") via Regex before sending to PAC. Match SAT blacklist/whitelist strictness.
    *   **Postal Code**: Validate against `c_CodigoPostal`.
    *   **ObjetoImp**:
        *   `02` (Sí objeto de impuesto) for **Honorarios Notariales**.
        *   `01` (No objeto de impuesto) or `ACuentaTerceros` node for **Suplidos/Gastos** (ISAI, Derechos Registro).
*   **Persona Moral Retentions (RFC Length == 12)**:
    *   **ISR**: 10% retention.
    *   **IVA**: 2/3 of IVA Trasladado (Use `10.6667%` for calculation precision).
*   **ISAI Manzanillo (Local Tax)**:
    *   Formula: `ISAI = Max(PrecioOperacion, ValorCatastral) * TasaManzanillo`
    *   Default Tasa: **3%** (Configurable via Remote Config).
*   **Copropiedad (Co-ownership)**:
    *   The sum of percentages in `DatosAdquirientesCopSC` MUST equal exactly **100.00%**.
    *   Validation: `abs(sum(percentages) - 100.0) < 0.001` is NOT allowed. It must be exact. If OCR reads 99.9%, the system must block/flag.

## 3. Technology Stack
*   **Language**: Python 3.11 (Backend), TypeScript/React (Frontend).
*   **Libraries**:
    *   `satcfdi` (CFDI 4.0 & Complemento Notarios).
    *   `fastapi` (API Framework).
    *   `spacy` (NLP).
    *   `pytesseract` (OCR).
    *   `google-cloud-secret-manager`.

## 4. Security
*   **Digital Lock**: Firestore rules must PREVENT updates to `expedientes` or `facturas` if `status == 'Timbrado'`.

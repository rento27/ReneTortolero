# Notaría 4 Digital Core - AGENTS.md

This file documents the architectural and fiscal constraints for the "Notaría 4 Digital Core" project. All changes must adhere to these rules.

## 1. Architectural Principles: "Serverless Sovereign"

*   **Infrastructure:** Hybrid Serverless.
    *   **Heavy Lifting (OCR, XML Signing, NLP):** Google Cloud Run (Python 3.11, FastAPI).
    *   **Event-Driven:** Firebase Cloud Functions (2nd Gen).
    *   **Database:** Cloud Firestore (Root collections: `clients`, `expedientes`, `facturas`).
    *   **Frontend:** React on Firebase Hosting.
*   **Sovereignty:** All data and logic reside in the Notary's own GCP project. No dependencies on third-party SaaS for core logic.
*   **Security:**
    *   **CSD Credentials (.key, password):** MUST be stored in **Google Secret Manager**.
    *   **Access:** Credentials must be loaded directly into memory. **NEVER** write `.key` files to disk or include them in the repo/image.
    *   **Digital Lock:** Once a status is "Timbrado", the record in Firestore is immutable.

## 2. Fiscal Logic & Validation (CRITICAL)

This system must act as a strict "Fiscal Auditor".

### 2.1 CFDI 4.0 Compliance
*   **Name Sanitization:** For the `Receptor` name, you MUST remove the corporate regime (e.g., "S.A. DE C.V.", "S C") using Regex. The name must match the SAT Constancia exactly (excluding regime).
*   **Zip Code:** Validate `DomicilioFiscalReceptor` against the SAT Catalog (`c_CodigoPostal`) ensuring it matches the state/municipality.

### 2.2 Retentions (Personas Morales)
*   **Trigger:** If `Len(RFC_Receptor) == 12` (Persona Moral).
*   **ISR:** Retain **10%** of the taxable base.
*   **IVA:** Retain **10.6667%** (Two-thirds of IVA).
*   **Precision:** Use `decimal` library with extended context (prec=10+) to avoid rounding errors. Do not use float.

### 2.3 ISAI Manzanillo (Local Tax)
*   **Formula:** `ISAI = Max(Precio_Operacion, Valor_Catastral) * Tasa_Manzanillo`
*   **Configuration:** `Tasa_Manzanillo` should be fetched from configuration (default 3% for 2025), not hardcoded permanently.

### 2.4 Copropiedad (Co-ownership)
*   **Validation:** The sum of percentages in `DatosAdquirientesCopSC` (Complemento) MUST equal **exactly 100.00%**.
*   **Action:** If sum != 100.00, the system must block the generation and raise an error.

### 2.5 Objeto de Impuesto (ObjetoImp)
*   **Honorarios:** `02` (Sí objeto de impuesto).
*   **Suplidos/Gastos:** `01` (No objeto de impuesto) OR use the `ACuentaTerceros` node.

## 3. Technology Stack & Standards

*   **Language:** Python 3.11 (Backend), TypeScript (Frontend).
*   **Key Libraries:**
    *   `satcfdi` (XML generation & signing).
    *   `spacy` (NLP).
    *   `fastapi` (API).
*   **Testing:** All fiscal logic must be unit tested. Precision is paramount.

# AGENTS.md - Notaría 4 Digital Core

This file outlines the critical architectural and fiscal constraints for the "Notaría 4 Digital Core" project. All changes must adhere to these rules.

## 1. Architecture Constraints
- **Model:** Serverless Sovereign (Firebase + Google Cloud Run).
- **Backend:** Python (FastAPI) on Cloud Run.
  - Handles heavy lifting: OCR (Tesseract), NLP (spaCy), XML Signing (`satcfdi`).
  - **Security:** Private Keys (.key) and CSD passwords must NEVER be hardcoded. Use Google Secret Manager.
- **Frontend:** React (SPA) on Firebase Hosting.
- **Database:** Cloud Firestore. Root collections: `clients`, `expedientes`, `facturas`.

## 2. Fiscal Logic & Validation (Strict)
### CFDI 4.0 Compliance
- **Name Sanitization:**
  - The `Nombre` attribute in `Receptor` must match the SAT database exactly.
  - **CRITICAL:** You must REMOVE the corporate regime (e.g., "S.A. DE C.V.", "S.C.") using Regex before sending to the PAC.
  - *Example:* "INMOBILIARIA DEL PACÍFICO, S.A. DE C.V." -> "INMOBILIARIA DEL PACIFICO".
- **Postal Code:** Must be cross-validated against the SAT `c_CodigoPostal` catalog.

### Taxes & Retentions
- **ObjectImp (Objeto de Impuesto):**
  - **Honorarios Notariales:** Code `02` (Sí objeto de impuesto).
  - **Suplidos/Gastos:** Code `01` (No objeto) OR use the `ACuentaTerceros` node.
- **Personas Morales (Legal Entities):**
  - **Trigger:** If `Len(RFC_Receptor) == 12`.
  - **ISR Retention:** 10% of the taxable base.
  - **IVA Retention:** Two-thirds (2/3) of the transferred IVA (~10.6667%).
  - **Precision:** Use `decimal` library with high precision context to avoid off-by-one cent errors.

### Local Taxes (Manzanillo)
- **ISAI (Impuesto Sobre Adquisición de Inmuebles):**
  - **Formula:** `Max(Price, CadastralValue) * Rate`.
  - The rate is managed via configuration (e.g., Firebase Remote Config), not hardcoded constants if possible, but the logic must support it.

### Copropiedad (Co-ownership)
- **Validation:** Sum of percentages in `DatosAdquirientesCopSC` must equal exactly `100.00%`.
- If sum != 100.00% (e.g., 99.9%), the system must BLOCK the operation.

## 3. Implementation Guidelines
- **Python:** Use type hints and Pydantic models.
- **Libraries:** Use `satcfdi` for XML generation.
- **Testing:** All fiscal logic must be unit tested (`pytest`).

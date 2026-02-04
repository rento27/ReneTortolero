# AGENTS.md for Notaría 4 Digital Core

This file outlines the strict architectural and fiscal constraints for the Notaría 4 Digital Core project. All changes within the `notaria_4_core/` directory must adhere to these rules.

## 1. Architectural Principles
- **Serverless Sovereign:** The system runs on a hybrid of Google Cloud Run (Heavy Processing - Python) and Firebase (Event-driven - Node.js).
- **Security First:** Private keys (`.key`) and CSD passwords MUST NEVER be stored in the code or filesystem. They must be retrieved from Google Secret Manager at runtime in memory.
- **Pydantic V2:** Use `model_dump()` instead of `.dict()` to avoid deprecation warnings.

## 2. Fiscal Validation Rules (CFDI 4.0)
- **Name Sanitization:** The `Nombre` attribute for the Receptor must match the SAT database exactly but **exclude** the corporate regime.
  - *Example:* "INMOBILIARIA DEL PACÍFICO, S.A. DE C.V." -> "INMOBILIARIA DEL PACIFICO".
  - Use regex to strip common regimes (S.A., S.C., S.A.P.I., etc.).
- **Postal Code:** Strict validation against SAT catalog `c_CodigoPostal` required before XML generation.
- **ObjectoImp (Tax Object):**
  - **Honorarios:** Must use `02` (Sí objeto de impuesto).
  - **Suplidos/Gastos:** Must use `01` (No objeto de impuesto) OR use the `ACuentaTerceros` node.
- **Decimal Precision:** Use `decimal.getcontext().prec = 50` to avoid rounding errors.

## 3. Specific Fiscal Logic (Manzanillo & Retentions)
- **Persona Moral Retentions (RFC length == 12):**
  - **ISR:** 10% of Subtotal.
  - **IVA:** Two-thirds of IVA (approx 10.6667%).
  - *Calculation:* `IVA_Ret = Subtotal * 0.106667` (Ensure precise rounding).
- **ISAI Manzanillo:**
  - Formula: `Max(OperationPrice, CadastralValue) * Rate`.
  - The rate is typically 3% but should be configurable.
- **Copropiedad (Co-ownership):**
  - The sum of percentages in `DatosAdquirientesCopSC` MUST equal exactly `100.00%`.
  - If the sum is `99.99%` or `100.01%`, validation must fail.

## 4. Code Structure
- **Backend:** Python 3.11 with FastAPI.
- **Libraries:** `satcfdi` (XML signing), `spacy` (NLP), `pytesseract` (OCR).

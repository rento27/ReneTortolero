# AGENTS.md - Notaría 4 Digital Core

## Scope
This document applies to the `notaria_4_core/` directory and all its subdirectories.

## Architectural Constraints (Serverless Sovereign)
1. **Backend:** Must be Python 3.11 running on Cloud Run (managed container).
2. **Frontend:** React (Vite) hosted on Firebase Hosting.
3. **Database:** Cloud Firestore.
4. **Secrets:** All private keys (.key), passwords, and certificates (.cer) MUST be accessed via Google Secret Manager. NEVER store them in the codebase or environment variables.

## Fiscal Rules (Strict Enforcement)
### CFDI 4.0
1. **Name Sanitization:** You MUST remove corporate regimes (e.g., "S.A. DE C.V.", "S.C.") from the `Receptor.Nombre`. The name must match the SAT database exactly but without the regime.
2. **Postal Code:** `DomicilioFiscalReceptor` must be validated against the SAT catalog `c_CodigoPostal`.
3. **ObjectImp:**
   - Honorarios: `02` (Sí objeto de impuesto).
   - Suplidos/Derechos: `01` (No objeto) OR use `ACuentaTerceros`.

### Retentions (Personas Morales)
- **Trigger:** If `len(RFC_Receptor) == 12`.
- **ISR:** 10% of Subtotal.
- **IVA:** 10.6667% (Two-thirds of 16%).
- **Precision:** Use `decimal` module with high precision to avoid off-by-one cent errors.

### Local Taxes (Manzanillo)
- **ISAI:** `Max(PrecioOperacion, ValorCatastral) * Tasa_Manzanillo`.
- `Tasa_Manzanillo` should be fetched from configuration (default ~3%).

## Code Style
- Python: Follow PEP 8. Use type hints.
- Frontend: Use Tailwind CSS.

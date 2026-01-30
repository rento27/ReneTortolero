# AGENTS.md - Notaría 4 Digital Core

## 1. Contexto y Soberanía
Este proyecto "Notaría 4 Digital Core" es una plataforma propietaria para la Notaría Pública No. 4 de Manzanillo, Colima. El objetivo es soberanía tecnológica y precisión fiscal absoluta.

## 2. Restricciones Técnicas
- **Lenguaje:** Python 3.11 para el backend (Cloud Run).
- **Librerías Clave:**
  - `satcfdi` para generación y timbrado de CFDI 4.0.
  - `spacy` y `pytesseract` para OCR y NLP.
  - `google-cloud-secret-manager` para gestión de llaves.
- **Base de Datos:** Firestore (NoSQL) con colecciones raíz: `clientes`, `expedientes`, `facturas`.
- **Infraestructura:** Google Cloud Run (Serverless) + Firebase Functions.

## 3. Reglas Fiscales (Estrictas)
### 3.1 Validaciones CFDI 4.0
- **Nombres:** Deben coincidir EXACTAMENTE con la constancia del SAT.
  - **REGLA CRÍTICA:** Se debe ELIMINAR el régimen societario (e.g., "S.A. DE C.V.") del nombre antes de timbrar. Usar Regex.
- **CP:** Validar contra catálogo `c_CodigoPostal`.
- **Decimales:** Usar `decimal` con contexto de alta precisión.

### 3.2 Impuestos y Retenciones
- **ObjetoImp:**
  - Honorarios -> `02` (Sí objeto).
  - Suplidos/Gastos -> `01` (No objeto) o nodo `ACuentaTerceros`.
- **Retenciones Persona Moral (RFC longitud 12):**
  - ISR: 10%
  - IVA: 10.6667% (Dos terceras partes).
- **ISAI Manzanillo:** `Max(PrecioOperacion, ValorCatastral) * Tasa`. La tasa se obtiene de configuración externa.

### 3.3 Complemento de Notarios
- **Copropiedad:** La suma de porcentajes en `DatosAdquirientesCopSC` debe ser EXACTAMENTE 100.00%. Si es 99.99% o 100.01%, debe fallar.

## 4. Seguridad
- **Secretos:** NUNCA hardcodear llaves privadas (.key) o contraseñas. Usar Secret Manager.
- **Integridad:** Una vez estatus "Timbrado", el expediente es inmutable (regla de Firestore).

## 5. Estilo de Código
- Usar `snake_case` para variables y funciones en Python.
- Documentar funciones complejas con Docstrings explicando la regla fiscal aplicada.

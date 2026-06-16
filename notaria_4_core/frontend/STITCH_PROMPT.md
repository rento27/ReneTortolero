# Prompt Maestro para Google Stitch: Notaría 4 Digital Core

**Objetivo General:**
Generar una Single Page Application (SPA) en React (usando Tailwind CSS) que sirva como la interfaz "Human-in-the-Loop" para el sistema operativo y fiscal "Notaría 4 Digital Core".

**Estética y Diseño:**
El diseño debe ser sobrio, institucional, serio y altamente operativo (orientado a productividad y alta densidad de datos). Utilizar una paleta de colores basada en tonos grises, blanco, azul marino institucional y acentos en verde oscuro (éxito/validado) y rojo oscuro (error fiscal). Tipografía legible y profesional (ej. Inter o Roboto).

## Flujo Principal: Human-in-the-Loop

La aplicación debe estructurarse en torno al ciclo de vida de un expediente notarial y la facturación CFDI 4.0. Se requieren las siguientes vistas/componentes principales:

### 1. Dashboard / Listado de Expedientes
- Una tabla que muestre los expedientes activos.
- Columnas: Número de Escritura, Cliente Principal, Fecha, Estatus (Borrador, Validado, Timbrado), Acciones.
- Botón principal: "Nuevo Expediente / Subir Documento".

### 2. Pantalla de Carga de Documentos (Upload)
- Zona de "Drag & Drop" para arrastrar archivos PDF (la escritura escaneada o nativa).
- Indicador visual de progreso: "Subiendo a Storage..." -> "Iniciando Extracción OCR/NLP en Cloud Run...".

### 3. Vista de Extracción OCR/NLP (Split-View)
- **Panel Izquierdo:** Visor de PDF embebido.
- **Panel Derecho:** Formulario de datos pre-llenados por la inteligencia artificial.
  - Secciones colapsables: `Datos de Escritura`, `Enajenantes (Vendedores)`, `Adquirentes (Compradores)`, `Inmuebles`, `Valores y Montos`.
- **Interacción Clave:** El usuario debe poder editar cualquier campo manualmente. Idealmente, visualmente se debe indicar (con un icono o color sutil) qué datos fueron extraídos automáticamente vs. editados por el humano.

### 4. Panel de Validación Fiscal (Ingeniería Fiscal)
Esta es la zona de rigor técnico. Debe contener:
- **Validación SAT:** Un componente que muestre el estatus de validación del RFC y Código Postal (indicando "Validado en catálogo SAT" en verde o "Discrepancia" en rojo).
- **Cálculo ISAI:** Formulario que muestre el "Precio de Operación", "Valor Catastral", la "Tasa Manzanillo" (fetch de Remote Config) y el resultado calculado.
- **Detalle de Conceptos (ObjetoImp):**
  - Tabla donde se listen los Honorarios (marcando visualmente que son `02 - Sí objeto`) y los Suplidos/Derechos (marcando `01 - No objeto`).
  - Cálculo automático de Retenciones (ISR 10%, IVA 10.6667%) si el cliente es Persona Moral.
- Mostrar una barra flotante o pie de página con los totales: Subtotal, Impuestos Trasladados, Retenciones, y Total.

### 5. Botón de Acción y Vista Previa (Generación)
- Botón principal: **"Generar CFDI y Complemento Notarial"**.
- Al hacer clic, debe mostrar un Modal de confirmación final.
- **Vista Previa Post-Generación:**
  - Pestañas para previsualizar:
    1. El XML sellado (formato código).
    2. El "PDF Fiscal" (CFDI estándar).
    3. El "Anexo Administrativo: Cuenta de Gastos" (Mostrando el "PDF Híbrido").

## Requisitos Técnicos para Stitch:
- Construir componentes modulares reutilizables.
- Preparar los `services` o llamadas a API (Axios/Fetch) apuntando a los endpoints del backend en FastAPI (e.g., `POST /api/v1/extract-data`, `POST /api/v1/cfdi`).
- Utilizar el contexto de React (o Zustand/Redux) para mantener el estado del expediente activo durante el flujo "Split-View".
- Mockear la respuesta del OCR inicial para que la UI pueda ser testeada y visualizada inmediatamente en el preview de Stitch antes de conectar al backend real.

# Notaría 4 Digital Core - Google Stitch UI Prompt

**Objective:**
Use this prompt in Google Stitch (stitch.withgoogle.com) to generate the React/Tailwind UI for the Notaría 4 Digital Core platform. Once generated, use an MCP-enabled agent (like Claude Code) to pull this design into the codebase.

---

## Stitch Prompt

Create a modern, professional, and highly functional web application interface for a Mexican Notary Public ("Notaría 4 Digital Core"). The design must be clean, using a trustworthy color palette (deep blues, clean whites, subtle grays, and professional accents) suitable for legal and fiscal software.

The application has three main screens:

### 1. Dashboard (Analytics & Overview)
- A sidebar navigation on the left with links: Dashboard, Expedientes (Deeds), Clientes, Facturación (Billing), and Configuración (Settings).
- The main content area should have a header displaying the Notary's name ("Notaría Pública No. 4 - Lic. René Manuel Tortolero Santillana") and a user profile avatar.
- Below the header, display a grid of 4 KPI cards:
  - "Facturado Hoy" (Billed Today) showing a currency amount.
  - "ISAI Acumulado" (Accumulated ISAI) showing a currency amount.
  - "Escrituras Procesadas" (Deeds Processed) showing an integer.
  - "Tasa ISAI Manzanillo" (Manzanillo ISAI Rate) showing a percentage (e.g., 3%).
- Below the KPIs, include a recent activity table showing the latest processed deeds with columns: Escritura, Cliente, Tipo de Acto, Estatus (Borrador, Validado, Timbrado), and Acciones.

### 2. "Human-in-the-Loop" Verification View (Split Screen)
This is the core feature. The screen should be split horizontally (50/50).
- **Left Pane (Document Viewer):** A visual representation of a PDF viewer containing a legal deed. It should have basic controls (zoom, pagination) and show simulated highlighted text in yellow (e.g., highlighting a name or a price), simulating AI OCR extraction.
- **Right Pane (CFDI 4.0 & Data Form):** A structured form to validate the data extracted from the PDF.
  - **Section A: Operación.** Fields for Escritura No., Fecha de Firma, Precio de Operación, Valor Catastral, and a calculated "ISAI Manzanillo" read-only field.
  - **Section B: Participantes.** Two lists: "Enajenantes" (Sellers) and "Adquirientes" (Buyers). Each item should show Name, RFC, CURP, and a "% Copropiedad" input field. Include a visual indicator that validates the sum equals 100%.
  - **Section C: Facturación.** Fields for Subtotal, Retención ISR, Retención IVA, and Total. Include a prominent "Timbrar CFDI 4.0" (Stamp CFDI 4.0) primary button.
- Interaction: Clicking a field in the Right Pane (e.g., Precio de Operación) should visually correspond to the highlighted text in the Left Pane.

### 3. Customer Delivery (WhatsApp Simulation)
- A modal or side-panel showing a preview of the automated WhatsApp message that will be sent to the client once the CFDI is stamped.
- The message template should read: "Estimado cliente de Notaría 4, su escritura [Número] ha sido facturada. Descargue su XML y PDF aquí: [Enlace]".
- Include a "Send via WhatsApp" button with the WhatsApp brand color.

**Styling Requirements:**
- Use Tailwind CSS.
- Ensure the layout is responsive, though optimized for desktop (given it's a professional tool).
- Emphasize clear typography, adequate padding, and distinct visual hierarchy to prevent errors in data entry.
- Use a "Toast" or alert component style for error messages (e.g., "Error: La suma de copropiedad no es 100%").

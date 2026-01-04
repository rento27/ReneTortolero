# Notaría 4 Digital Core

## Overview
A sovereign platform for Notaría Pública No. 4 de Manzanillo, Colima.
Built on **Google Firebase** and **Google Cloud Run**.

## Architecture
- **Frontend**: React (Vite) hosted on Firebase Hosting.
- **Backend**: Python (FastAPI) on Cloud Run.
  - OCR: Tesseract
  - NLP: spaCy
  - Fiscal: satcfdi (CFDI 4.0)

## Components
- `fiscal_engine.py`: Manzanillo ISAI (3%), Persona Moral Retentions.
- `xml_generator.py`: CFDI 4.0 generation logic.
- `extraction_engine.py`: PDF -> Text (PyMuPDF -> Tesseract).

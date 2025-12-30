# Notaría 4 Digital Core

## Overview
A proprietary platform designed for **Notaría Pública No. 4 de Manzanillo**, replacing generic SaaS solutions with a sovereign, serverless architecture on **Google Firebase** and **Google Cloud Platform (GCP)**.

## Architecture: "Serverless Sovereign"

### 1. Frontend
- **Tech**: React (Vite) + Tailwind CSS
- **Hosting**: Firebase Hosting
- **Role**: Single Page Application for deed validation ("Human-in-the-Loop") and dashboarding.

### 2. Backend (Hybrid)
- **Cloud Run (Python)**:
  - Docker container running FastAPI.
  - Handles heavy loads: Tesseract OCR, spaCy NLP, and `satcfdi` XML generation.
  - **Why?**: Requires system dependencies (libxml2, tesseract) not available in standard Cloud Functions.
- **Firebase Cloud Functions (Node.js/Python)**:
  - Event triggers (e.g., WhatsApp notifications on Firestore writes).

### 3. Data & Storage
- **Firestore**: NoSQL database for flexible deed/invoice structures.
- **Cloud Storage**: Secure storage for PDF deeds and generated XML/PDF invoices.

### 4. Security
- **Secret Manager**: Stores CSD (Certificado Sello Digital) private keys. Keys are accessed only in memory by the Cloud Run service.

## Core Features

1.  **Fiscal Rules Engine**:
    - Automatic detection of "Persona Moral" (12 char RFC).
    - Auto-calculation of retentions (ISR 10%, IVA 10.6667%).
    - "Sanitization" of names (Removing "S.A. de C.V.").
    - **Manzanillo ISAI**: Hardcoded local logic (`Max(Precio, ValorCatastral) * 0.03`).

2.  **Intelligent Extraction**:
    - **PyMuPDF**: Fast text extraction for digital native PDFs.
    - **Tesseract OCR**: Fallback for scanned documents.
    - **spaCy NLP**: Entity recognition for Vendedor/Adquirente/Monto.

3.  **Legal Certainty**:
    - **NOM-151**: Blockchain-style time-stamping for internal receipts.
    - **Digital Lock**: Firestore rules prevent editing "Timbrado" deeds.

## Project Structure

```
notaria-4-core/
├── backend/            # Cloud Run Service (Python)
│   ├── Dockerfile
│   ├── main.py         # FastAPI Entry point
│   └── lib/            # Business Logic
│       ├── fiscal_engine.py # Tax calculations
│       └── security.py      # Secret Manager
├── frontend/           # React SPA
│   ├── src/
│   │   ├── App.jsx     # Split-screen UI
│   │   └── ...
│   └── ...
├── firebase.json       # Firebase Hosting/Firestore config
└── firestore.rules     # Security Rules
```

## Deployment Roadmap

1.  **Phase 1 (Foundations)**: Cloud Run setup, Python Fiscal Engine, Basic UI.
2.  **Phase 2 (Intelligence)**: Tesseract/spaCy integration, Full Frontend.
3.  **Phase 3 (Perfection)**: WhatsApp API, NOM-151, Production Go-Live.

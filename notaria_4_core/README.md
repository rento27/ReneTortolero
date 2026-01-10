# Deployment Guide for Notaría 4 Digital Core

This system follows the "Serverless Sovereign" architecture using Google Cloud Platform.

## 1. Backend Deployment (Cloud Run)

The backend performs OCR, NLP, and Fiscal Calculations. It is containerized to support system dependencies (Tesseract, libgl1).

### Prerequisites
*   Google Cloud SDK installed.
*   Docker installed.

### Steps
1.  **Build the Container:**
    ```bash
    gcloud builds submit --tag gcr.io/[PROJECT_ID]/notaria-core-backend ./backend
    ```

2.  **Deploy to Cloud Run:**
    ```bash
    gcloud run deploy notaria-core-backend \
      --image gcr.io/[PROJECT_ID]/notaria-core-backend \
      --platform managed \
      --region us-central1 \
      --memory 2Gi \
      --timeout 300 \
      --allow-unauthenticated
    ```

3.  **Secrets Configuration:**
    Ensure the Service Account used by Cloud Run has access to Secret Manager.
    *   Upload `.key`, `.cer`, and password to Secret Manager.
    *   Grant `Secret Manager Secret Accessor` role to the Cloud Run service account.

## 2. Frontend Deployment (Firebase Hosting)

The frontend is a React SPA.

### Steps
1.  **Install Dependencies:**
    ```bash
    cd frontend
    npm install
    ```

2.  **Build:**
    ```bash
    npm run build
    ```

3.  **Deploy:**
    ```bash
    firebase deploy --only hosting
    ```

## 3. Configuration

*   **Firebase Remote Config:** Set `tesseract_enabled` (bool) and `isai_rate_manzanillo` (number) in the Firebase Console.
*   **Firestore:** Ensure indexes are created for `expedientes` based on status and date.

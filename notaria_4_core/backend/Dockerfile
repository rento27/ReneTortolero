# Dockerfile for Notaría 4 Digital Core (Cloud Run)
FROM python:3.11-slim

# Install system dependencies for OCR and XML processing
# tesseract-ocr: For OCR fallback
# tesseract-ocr-spa: Spanish language pack for Tesseract
# libgl1: Required by some CV libraries (if used) or PyMuPDF dependencies
# libxml2-dev, libxslt-dev: For satcfdi/lxml performance
RUN apt-get update && apt-get install -y \
    tesseract-ocr \
    tesseract-ocr-spa \
    libgl1 \
    libglib2.0-0 \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Download Spacy Model
RUN python -m spacy download es_core_news_lg

# Copy application code
COPY . .

# Environment variables (Defaults, override in Cloud Run)
ENV PORT=8080

# Run with Uvicorn
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8080"]

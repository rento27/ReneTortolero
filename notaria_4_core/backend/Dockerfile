FROM python:3.11-slim

# Install system dependencies for OCR, PDF processing, and XML signing
RUN apt-get update && apt-get install -y \
    tesseract-ocr \
    tesseract-ocr-spa \
    libgl1 \
    libglib2.0-0 \
    libxml2 \
    libxslt1-dev \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Download Spacy model (can be optimized later)
RUN python -m spacy download es_core_news_lg

COPY . .

# Expose port (Cloud Run expects $PORT, defaulting to 8080)
CMD exec uvicorn main:app --host 0.0.0.0 --port ${PORT:-8080}

FROM python:3.11-slim

# Install system dependencies
# tesseract-ocr: For OCR (Extraction Engine)
# libgl1, libglib2.0-0: Often required by computer vision libraries (like cv2 or some pdf tools)
# libxml2, libxslt1-dev: Required for XML processing performance and weasyprint
RUN apt-get update && apt-get install -y \
    tesseract-ocr \
    tesseract-ocr-spa \
    libgl1 \
    libglib2.0-0 \
    libxml2 \
    libxslt1-dev \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Copy requirements and install
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Download spaCy model
RUN python -m spacy download es_core_news_lg

# Copy application code
COPY . .

# Run the web service on container startup.
# Cloud Run sets the PORT environment variable (default 8080)
CMD exec uvicorn main:app --host 0.0.0.0 --port ${PORT:-8080}

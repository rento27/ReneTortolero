FROM python:3.11-slim

# Install system dependencies for OCR and PDF processing
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

# Download spaCy model (using small for init, spec mentions lg)
RUN python -m spacy download es_core_news_lg

COPY . .

# Expose port
ENV PORT=8080

# Run with uvicorn
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8080"]

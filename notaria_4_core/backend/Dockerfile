FROM python:3.11-slim

# Install system dependencies for OCR and XML processing
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

# Download Spacy model (can be optimized later)
RUN python -m spacy download es_core_news_lg

# Copy application code
COPY . .

# Expose port (Cloud Run defaults to 8080)
ENV PORT=8080
EXPOSE 8080

# Start command
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8080"]

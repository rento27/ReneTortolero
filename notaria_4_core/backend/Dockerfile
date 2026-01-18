FROM python:3.11-slim

# Install system dependencies
# tesseract-ocr: for OCR
# libgl1, libglib2.0-0: often required for image processing libraries
# libxml2, libxslt: for XML processing (satcfdi/lxml)
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

# Download spaCy model (es_core_news_lg is large, using sm for base or lg if requested.
# Prompt mentioned fine-tuning on es_core_news_lg)
# Using python -m spacy download es_core_news_lg
RUN python -m spacy download es_core_news_lg

# Copy application code
COPY . .

# Expose port
EXPOSE 8080

# Run command
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8080"]

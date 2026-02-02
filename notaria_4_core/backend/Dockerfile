FROM python:3.11-slim

# Install system dependencies for OCR, PDF generation, and image processing
# libgl1 and libglib2.0-0 are for cv2/image processing
# tesseract-ocr is for OCR
# tesseract-ocr-spa is the Spanish language pack
RUN apt-get update && apt-get install -y \
    tesseract-ocr \
    tesseract-ocr-spa \
    libgl1 \
    libglib2.0-0 \
    libpango-1.0-0 \
    libharfbuzz0b \
    libpangoft2-1.0-0 \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Copy requirements and install
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Download spaCy Spanish model
RUN python -m spacy download es_core_news_lg

# Copy application code
COPY . .

# Environment variables
ENV PORT=8080

# Command to run the application
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8080"]

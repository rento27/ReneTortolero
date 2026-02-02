# Use official Python 3.11 slim image
FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Install system dependencies required for OCR and PDF processing
# tesseract-ocr: for optical character recognition
# tesseract-ocr-spa: Spanish language pack for Tesseract
# libgl1: required by cv2 (often used by OCR libs)
# libglib2.0-0: required by some PDF/Image libraries
RUN apt-get update && apt-get install -y \
    tesseract-ocr \
    tesseract-ocr-spa \
    libgl1 \
    libglib2.0-0 \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements file
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Download spaCy Spanish model
RUN python -m spacy download es_core_news_lg

# Copy the rest of the application code
COPY . .

# Expose the port
EXPOSE 8080

# Command to run the application
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8080"]

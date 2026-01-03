# Use official Python 3.11 slim image
FROM python:3.11-slim

# Install system dependencies for Tesseract and GL (needed for PyMuPDF/OpenCV sometimes)
RUN apt-get update && apt-get install -y \
    tesseract-ocr \
    tesseract-ocr-spa \
    libgl1 \
    libglib2.0-0 \
    && rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /app

# Install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Download spaCy model (Spanish Large as per spec)
# Using 'sm' for build speed in prototype, but commented 'lg' for production
RUN python -m spacy download es_core_news_sm
# RUN python -m spacy download es_core_news_lg

# Copy application code
COPY . .

# Expose port (Cloud Run uses 8080 by default)
EXPOSE 8080

# Command to run the application
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8080"]

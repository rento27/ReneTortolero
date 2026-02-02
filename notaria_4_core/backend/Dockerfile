# Use Python 3.11 slim as base
FROM python:3.11-slim

# Install system dependencies for Tesseract, PyMuPDF, and XML processing
RUN apt-get update && apt-get install -y \
    tesseract-ocr \
    tesseract-ocr-spa \
    libgl1 \
    libglib2.0-0 \
    libxml2 \
    libxslt1-dev \
    && rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /app

# Copy requirements and install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code contents to /app
# This puts main.py at /app/main.py and lib/ at /app/lib/
COPY . .

# Expose port (Cloud Run defaults to 8080)
EXPOSE 8080

# Run FastAPI with Uvicorn
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8080"]

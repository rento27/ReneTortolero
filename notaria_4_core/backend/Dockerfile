# notaria_4_core/backend/Dockerfile
FROM python:3.11-slim

# Install system dependencies for OCR and generic processing
RUN apt-get update && apt-get install -y \
    tesseract-ocr \
    tesseract-ocr-spa \
    libgl1 \
    libglib2.0-0 \
    libxml2 \
    libxslt1-dev \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Copy requirements first to leverage Docker cache
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of the application
COPY . .

# Expose port (Cloud Run defaults to 8080)
ENV PORT=8080
CMD exec uvicorn main:app --host 0.0.0.0 --port ${PORT}

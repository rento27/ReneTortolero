FROM python:3.11-slim

# Install system dependencies
RUN apt-get update && apt-get install -y \
    tesseract-ocr \
    tesseract-ocr-spa \
    libgl1 \
    libglib2.0-0 \
    libxml2 \
    libxslt1-dev \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Download spaCy model (Spanish large)
RUN python -m spacy download es_core_news_lg

# Copy application code
COPY . .

# Expose port
ENV PORT 8080

# Run command
CMD exec uvicorn main:app --host 0.0.0.0 --port ${PORT}

FROM python:3.11-slim

# Install system dependencies for Tesseract and PyMuPDF/OpenCV if needed
RUN apt-get update && apt-get install -y \
    tesseract-ocr \
    libgl1 \
    libglib2.0-0 \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Copy requirements and install
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Download spaCy model (Spanish Large)
RUN python -m spacy download es_core_news_lg

COPY . .

# Expose port (Cloud Run uses 8080 by default)
ENV PORT=8080
EXPOSE 8080

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8080"]

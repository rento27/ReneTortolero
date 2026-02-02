FROM python:3.11-slim

# Install system dependencies for Tesseract and PyMuPDF/lxml
RUN apt-get update && apt-get install -y \
    tesseract-ocr \
    libgl1 \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Download spanish language model for spacy
RUN python -m spacy download es_core_news_lg

COPY . .

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8080"]

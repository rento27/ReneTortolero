FROM python:3.11-slim

# Install system dependencies
# tesseract-ocr: for OCR
# libgl1, libglib2.0-0: common libraries for image processing
# libxml2, libxslt1-dev: for lxml (used by satcfdi)
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

# Download spacy model (Spanish Large)
RUN python -m spacy download es_core_news_lg

# Copy the rest of the application
COPY . .

# Expose port
EXPOSE 8080

# Command to run the application
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8080"]

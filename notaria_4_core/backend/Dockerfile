# Use an official Python runtime as a parent image
FROM python:3.11-slim

# Install system dependencies for Tesseract (OCR) and PDF processing
RUN apt-get update && apt-get install -y \
    tesseract-ocr \
    tesseract-ocr-spa \
    libgl1 \
    libglib2.0-0 \
    && rm -rf /var/lib/apt/lists/*

# Set the working directory in the container
WORKDIR /app

# Copy the requirements file into the container
COPY requirements.txt .

# Install any needed packages specified in requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# Download spaCy model
RUN python -m spacy download es_core_news_lg

# Copy the current directory contents into the container at /app
COPY . .

# Expose port 8080 for Cloud Run
EXPOSE 8080

# Run main.py using uvicorn
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8080"]

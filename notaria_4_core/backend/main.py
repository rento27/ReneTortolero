from fastapi import FastAPI
import os

app = FastAPI(title="Notaria 4 Digital Core API")

@app.get("/")
async def root():
    """Root endpoint for basic verification."""
    return {"message": "Notaria 4 Digital Core API is running"}

@app.get("/health")
async def health_check():
    """Health check endpoint for Cloud Run."""
    return {"status": "healthy"}

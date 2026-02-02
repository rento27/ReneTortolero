from fastapi import FastAPI
import os

app = FastAPI(title="Notaria 4 Digital Core API", version="0.1.0")

@app.get("/")
def read_root():
    return {"status": "ok", "service": "Notaria 4 Digital Core Backend"}

@app.get("/health")
def health_check():
    return {"status": "healthy"}

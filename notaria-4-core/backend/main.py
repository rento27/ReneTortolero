from fastapi import FastAPI
import os

app = FastAPI(title="Notaria 4 Digital Core", version="1.0.0")

@app.get("/")
def health_check():
    return {"status": "ok", "service": "Notaria 4 Digital Core Backend"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=int(os.environ.get("PORT", 8080)))

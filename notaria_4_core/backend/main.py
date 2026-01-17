from fastapi import FastAPI, UploadFile, File, HTTPException
from pydantic import BaseModel
from typing import List, Optional
from decimal import Decimal
import os
import shutil

from lib.fiscal_engine import calculate_retentions, calculate_isai, sanitize_name, validate_copropiedad
from lib.extraction_engine import extract_text_from_pdf, analyze_deed_text

app = FastAPI(title="Notaria 4 Digital Core API")

class FiscalRequest(BaseModel):
    subtotal: Decimal
    receiver_rfc: str
    price: Optional[Decimal] = None
    cadastral_value: Optional[Decimal] = None
    isai_rate: Optional[Decimal] = Decimal("0.03")

@app.get("/")
async def health_check():
    return {"status": "ok", "service": "Notaria 4 Core", "version": "1.0.0"}

@app.post("/calculate-fiscal")
async def calculate_fiscal(request: FiscalRequest):
    """
    Calculates taxes and retentions based on input data.
    """
    retentions = calculate_retentions(request.subtotal, request.receiver_rfc)

    response = {
        "retentions": retentions,
        "isai": None
    }

    if request.price is not None and request.cadastral_value is not None:
        response["isai"] = calculate_isai(request.price, request.cadastral_value, request.isai_rate)

    return response

@app.post("/sanitize-name")
async def api_sanitize_name(name: str):
    return {"original": name, "sanitized": sanitize_name(name)}

@app.post("/upload-deed")
async def upload_deed(file: UploadFile = File(...)):
    """
    Receives a PDF deed, saves it temporarily, and runs extraction.
    """
    temp_path = f"/tmp/{file.filename}"
    try:
        with open(temp_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)

        text = extract_text_from_pdf(temp_path)
        data = analyze_deed_text(text)

        # Cleanup
        os.remove(temp_path)

        return {"filename": file.filename, "extracted_data": data, "text_preview": text[:200]}

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=int(os.environ.get("PORT", 8080)))

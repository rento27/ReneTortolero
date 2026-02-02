from fastapi import FastAPI, HTTPException, Request, UploadFile, File
from fastapi.responses import JSONResponse
from lib.fiscal_engine import FiscalEngine
from lib.extraction_engine import ExtractionEngine
from lib.xml_generator import XMLGenerator
import shutil
import os

app = FastAPI(title="Notaria 4 Digital Core API")

# Initialize engines
fiscal_engine = FiscalEngine()
extraction_engine = ExtractionEngine()

@app.get("/")
async def root():
    return {"status": "active", "system": "Notaria 4 Digital Core", "version": "1.0.0"}

@app.post("/calculate-taxes")
async def calculate_taxes(request: Request):
    """
    Calculates taxes based on the provided data, including Persona Moral retention and ISAI.
    """
    data = await request.json()
    try:
        result = fiscal_engine.calculate_total(data)
        return JSONResponse(content=result)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.post("/extract-data")
async def extract_data(file: UploadFile = File(...)):
    """
    Extracts data from an uploaded PDF/Image using OCR and NLP.
    """
    try:
        # Read file content into memory
        contents = await file.read()

        # Determine extraction strategy based on content type or extension
        # For now, treat everything as PDF or Image bytes handled by the engine
        text = extraction_engine.extract_text_from_pdf(contents)
        entities = extraction_engine.extract_entities(text)

        return {
            "filename": file.filename,
            "extracted_text_preview": text[:200] + "...",
            "entities": entities,
            "full_text_length": len(text)
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/generate-xml")
async def generate_xml(request: Request):
    """
    Generates a CFDI 4.0 XML based on verified data.
    """
    data = await request.json()
    try:
        generator = XMLGenerator()
        # Mocking the signer loading for now as we don't have secrets locally
        # generator.load_signer()
        xml_content = generator.create_cfdi(data)
        return {"xml": xml_content}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8080)

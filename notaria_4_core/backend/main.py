from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from decimal import Decimal
from typing import Optional
from lib.fiscal_engine import sanitize_name, calculate_retentions, calculate_isai_manzanillo

app = FastAPI(title="Notaría 4 Digital Core API")

class NameRequest(BaseModel):
    name: str

class FiscalCalcRequest(BaseModel):
    subtotal: float
    rfc_receptor: str

class IsaiRequest(BaseModel):
    precio_operacion: float
    valor_catastral: float
    tasa: Optional[float] = 0.03

@app.get("/health")
def health_check():
    return {"status": "ok", "service": "notaria_4_core_backend"}

@app.post("/sanitize-name")
def sanitize_name_endpoint(request: NameRequest):
    """
    Sanitizes a name for CFDI 4.0 (removes regime).
    """
    clean = sanitize_name(request.name)
    return {"original": request.name, "sanitized": clean}

@app.post("/calculate-fiscal")
def calculate_fiscal_endpoint(request: FiscalCalcRequest):
    """
    Calculates retentions based on RFC type.
    """
    try:
        subtotal_dec = Decimal(str(request.subtotal))
        results = calculate_retentions(subtotal_dec, request.rfc_receptor)
        return results
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.post("/isai-calc")
def isai_endpoint(request: IsaiRequest):
    """
    Calculates ISAI for Manzanillo.
    """
    try:
        p_op = Decimal(str(request.precio_operacion))
        v_cat = Decimal(str(request.valor_catastral))
        tasa = Decimal(str(request.tasa))

        isai = calculate_isai_manzanillo(p_op, v_cat, tasa)
        return {
            "base_gravable": float(max(p_op, v_cat)),
            "isai_calculated": float(isai)
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8080)

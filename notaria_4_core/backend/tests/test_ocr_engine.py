from notaria_4_core.backend.lib.ocr_engine import extract_structured_data

def test_extract_fallback():
    text = "COMPARECE JUAN PEREZ, LUEGO COMPRA MARIA GOMEZ. ESCRITURA 12345 RFC JUPJ800101XYZ"
    res = extract_structured_data(text)
    print(res)

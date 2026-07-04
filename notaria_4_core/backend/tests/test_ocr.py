from notaria_4_core.backend.lib.ocr_engine import extract_structured_data

def test_extract_structured_data_regex():
    text = "INSTRUMENTO NUM. 12345 RFC: ABC123456T12 y otro rfc DEF123456T12"
    data = extract_structured_data(text)

    assert data["escritura"] == "12345"
    assert "ABC123456T12" in data["rfcs"]
    assert "DEF123456T12" in data["rfcs"]

def test_extract_structured_data_fallback():
    text = "COMPARECE JUAN PEREZ Y MARIA LOPEZ COMPRA CARLOS SLIM"
    data = extract_structured_data(text)

    assert "JUAN PEREZ Y MARIA LOPEZ" in data["vendedores"][0]
    assert "CARLOS SLIM" in data["adquirientes"][0]

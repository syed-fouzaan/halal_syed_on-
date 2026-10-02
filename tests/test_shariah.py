import pandas as pd
from src.shariah.checks import screen_holdings_for_prohibited_sectors, calculate_purification_amount
from src.shariah.changes import detect_document_hash_changes
from src.shariah.documents import chunk_document_text

def test_screen_holdings_prohibited_detected():
    df = pd.DataFrame([
        {"company_name": "Infosys Ltd.", "sector": "Information Technology", "weight_pct": 5.0},
        {"company_name": "ABC Commercial Bank", "sector": "Banking", "weight_pct": 3.0}
    ])
    res = screen_holdings_for_prohibited_sectors(df)
    assert res["passed"] is False
    assert len(res["violations"]) == 1
    assert "Banking" in res["violations"][0]["sector"]

def test_screen_holdings_compliant():
    df = pd.DataFrame([
        {"company_name": "Infosys Ltd.", "sector": "Information Technology", "weight_pct": 8.0},
        {"company_name": "Sun Pharma", "sector": "Healthcare", "weight_pct": 6.0}
    ])
    res = screen_holdings_for_prohibited_sectors(df)
    assert res["passed"] is True
    assert len(res["violations"]) == 0

def test_purification_calculation():
    res = calculate_purification_amount(dividend_amount=1000.0, purification_ratio_pct=1.5)
    assert res["purification_payable"] == 15.0
    assert res["net_halal_dividend"] == 985.0

def test_chunk_document_text():
    text = "## Sector Mandate\nShariah compliance strictly prohibits riba and alcohol.\n\n## Screening\nDebt under 33%."
    chunks = chunk_document_text("DOC_TEST", text)
    assert len(chunks) >= 1
    assert "document_id" in chunks[0]
    assert "content_hash" in chunks[0]

from src.ingestion.amfi_nav import parse_amfi_nav_txt

def test_parse_amfi_nav_txt():
    sample_txt = """
    119172;INF277K01NG4;INF277K01NH2;Tata Ethical Fund - Direct Plan - Growth;395.7253;01-Oct-2026
    112090;INF174K01336;;Kotak Flexi Cap Fund - Regular Plan - Growth;80.4960;01-Oct-2026
    """
    res = parse_amfi_nav_txt(sample_txt, target_code="119172")
    assert len(res) == 1
    assert res[0]["amfi_code"] == "119172"
    assert res[0]["nav"] == 395.7253
    assert res[0]["isin"] == "INF277K01NG4"

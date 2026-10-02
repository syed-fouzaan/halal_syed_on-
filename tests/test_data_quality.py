import duckdb
from src.database.schema import init_schema
from src.database.repositories import Repository
from src.validation.data_quality import run_data_quality_checks

def test_data_quality_on_memory_db():
    conn = duckdb.connect(":memory:")
    init_schema(conn)
    repo = Repository(conn)
    
    # Register test fund
    repo.upsert_fund({
        "fund_id": "TEST_FUND",
        "scheme_name": "Test Fund Direct",
        "active": True
    })

    # Add valid transaction
    repo.add_transaction({
        "transaction_id": "TX_1",
        "fund_id": "TEST_FUND",
        "transaction_date": "2024-01-05",
        "transaction_type": "SIP",
        "amount": 2000.0,
        "units": 10.0,
        "nav": 200.0,
        "fees": 0.0,
        "source": "MANUAL"
    })

    # Add valid NAV
    repo.upsert_nav("TEST_FUND", "2024-01-05", 200.0, "SOURCE", "hash123")

    report = run_data_quality_checks(conn, "TEST_FUND")
    assert report["fund_id"] == "TEST_FUND"
    assert report["fail_count"] == 0
    assert report["status"] in ("PASS", "WARNING")

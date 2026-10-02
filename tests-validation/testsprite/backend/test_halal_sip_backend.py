"""
TestSprite Backend Verification Test for Halal SIP AI System.
Validates core database, deterministic valuation, XIRR solver, Shariah screening,
and data provenance.
"""
import sys
from pathlib import Path
from datetime import date

# Add project root to sys.path
PROJECT_ROOT = Path(__file__).parent.parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from src.database.connection import get_db_connection
from src.database.repositories import Repository
from src.calculations.portfolio import calculate_portfolio_summary
from src.calculations.returns import calculate_returns
from src.calculations.xirr import calculate_xirr
from src.calculations.sip import reconcile_sip_status
from src.shariah.checks import screen_holdings_for_prohibited_sectors, calculate_purification_amount
from src.validation.data_quality import run_data_quality_checks
from src.ai.ollama_client import OllamaClient
from src.ai.analyzer import AIAnalyzer

def test_duckdb_and_fund_integrity() -> None:
    conn = get_db_connection("data/database/halal_sip.duckdb")
    repo = Repository(conn)
    fund = repo.get_fund("TATA_ETHICAL_GROWTH_DIRECT")
    assert fund is not None, "Tata Ethical Fund must be registered in DuckDB"
    assert fund["scheme_name"] == "Tata Ethical Fund - Direct Plan - Growth"
    assert fund["active"] is True
    conn.close()
    print("[PASS] test_duckdb_and_fund_integrity")

def test_deterministic_valuation() -> None:
    txs = [
        {"transaction_type": "SIP", "transaction_date": "2024-01-05", "amount": 2000.0, "units": 5.0, "fees": 0.0},
        {"transaction_type": "SIP", "transaction_date": "2024-02-05", "amount": 2000.0, "units": 5.0, "fees": 0.0}
    ]
    summary = calculate_portfolio_summary(txs, latest_nav=450.0)
    assert summary["total_units"] == 10.0, f"Expected 10.0 units, got {summary['total_units']}"
    assert summary["current_value"] == 4500.0, f"Expected 4500.0 value, got {summary['current_value']}"
    assert summary["net_invested"] == 4000.0

    ret = calculate_returns(summary["current_value"], summary["net_invested"])
    assert ret["gain"] == 500.0
    assert ret["return_pct"] == 12.5
    print("[PASS] test_deterministic_valuation")

def test_xirr_root_finder() -> None:
    # 1-year investment with 15% return
    cfs = [
        (date(2023, 1, 1), -10000.0),
        (date(2024, 1, 1), 11500.0)
    ]
    rate = calculate_xirr(cfs)
    assert rate is not None, "XIRR calculation should converge"
    assert abs(rate - 0.15) < 0.01, f"Expected ~0.15, got {rate}"
    print("[PASS] test_xirr_root_finder")

def test_shariah_screening_and_purification() -> None:
    conn = get_db_connection("data/database/halal_sip.duckdb")
    repo = Repository(conn)
    holdings = repo.get_latest_holdings("TATA_ETHICAL_GROWTH_DIRECT")
    assert not holdings.empty, "Portfolio holdings must not be empty"

    screen_res = screen_holdings_for_prohibited_sectors(holdings)
    assert screen_res["passed"] is True, f"Screening failed: {screen_res['violations']}"
    assert len(screen_res["violations"]) == 0

    purif = calculate_purification_amount(dividend_amount=1000.0, purification_ratio_pct=1.5)
    assert purif["purification_payable"] == 15.0
    assert purif["net_halal_dividend"] == 985.0
    conn.close()
    print("[PASS] test_shariah_screening_and_purification")

def test_data_quality_audit() -> None:
    conn = get_db_connection("data/database/halal_sip.duckdb")
    dq = run_data_quality_checks(conn, "TATA_ETHICAL_GROWTH_DIRECT")
    assert dq["status"] in ("PASS", "WARNING"), f"Data quality check failed: {dq}"
    assert dq["fail_count"] == 0, f"Expected 0 failures, got {dq['fail_count']}"
    conn.close()
    print("[PASS] test_data_quality_audit")

def test_ai_graceful_degradation() -> None:
    client = OllamaClient(host="http://127.0.0.1:11434")
    # Even if Ollama is not running, generate should return error without throwing uncaught exception
    res = client.generate("Test prompt")
    assert "text" in res
    assert "error" in res
    print("[PASS] test_ai_graceful_degradation")

if __name__ == "__main__":
    print("=" * 60)
    print("Running TestSprite Backend Verification Suite...")
    print("=" * 60)
    test_duckdb_and_fund_integrity()
    test_deterministic_valuation()
    test_xirr_root_finder()
    test_shariah_screening_and_purification()
    test_data_quality_audit()
    test_ai_graceful_degradation()
    print("=" * 60)
    print("ALL 6 TESTSPRITE BACKEND VERIFICATION CHECKS PASSED!")
    print("=" * 60)

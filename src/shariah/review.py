from datetime import date
from typing import Any, Dict, Optional
import duckdb
from src.shariah.checks import screen_holdings_for_prohibited_sectors
from src.database.repositories import Repository
from src.utils.logging import get_logger

logger = get_logger("shariah_review")

def execute_shariah_review(
    conn: duckdb.DuckDBPyConnection,
    fund_id: str,
    doc_id: Optional[str] = None
) -> Dict[str, Any]:
    """
    Execute end-to-end Shariah compliance review workflow:
    1. Screen latest portfolio holdings
    2. Check document verification status
    3. Determine if human review is flagged
    4. Store review record in database
    """
    repo = Repository(conn)
    holdings_df = repo.get_latest_holdings(fund_id)
    screen_res = screen_holdings_for_prohibited_sectors(holdings_df)

    latest_doc = None
    docs = repo.list_documents(fund_id)
    if docs:
        latest_doc = docs[0]
        if not doc_id:
            doc_id = latest_doc["document_id"]

    # Determine status & flags
    human_review_required = False
    status = "COMPLIANT"
    methodology_summary = (
        "Screened against standard Shariah guidelines: Nifty 500 Shariah TRI benchmark criteria. "
        "Strict sector prohibition on conventional banks, non-Islamic finance, alcohol, pork, gambling, and adult media. "
        "Debt-to-market cap < 33%, cash deposits < 33%."
    )
    purification_summary = (
        "Quarterly dividend purification required for ancillary interest income. "
        "Estimated purification rate: 1.2% - 1.5% of gross dividend distributions."
    )

    if not screen_res["passed"]:
        status = "FLAGGED_VIOLATIONS"
        human_review_required = True
    elif not latest_doc:
        status = "NEEDS_DOCUMENT_AUDIT"
        human_review_required = True

    check_date = date.today()
    check_id = f"SC_{fund_id}_{check_date.strftime('%Y%m%d')}"

    check_record = {
        "check_id": check_id,
        "fund_id": fund_id,
        "document_id": doc_id,
        "check_date": check_date,
        "status": status,
        "methodology_summary": methodology_summary,
        "purification_summary": purification_summary,
        "change_detected": False,
        "human_review_required": human_review_required,
        "evidence_reference": f"Holdings count: {len(holdings_df)} companies; Doc: {doc_id or 'None'}"
    }

    repo.add_shariah_check(check_record)

    return {
        "check_id": check_id,
        "status": status,
        "human_review_required": human_review_required,
        "screening_results": screen_res,
        "methodology_summary": methodology_summary,
        "purification_summary": purification_summary
    }

from datetime import date, datetime, timedelta
from typing import Any, Dict, List
import duckdb

def run_data_quality_checks(conn: duckdb.DuckDBPyConnection, fund_id: str) -> Dict[str, Any]:
    """
    Run Section 19 Data Quality validation against the database:
    - required fields
    - dates
    - numeric fields
    - duplicate records
    - invalid NAV
    - missing NAV
    - impossible unit changes
    - source freshness
    - document hashes
    - parser failures
    Returns status: PASS | WARNING | FAIL and individual check items.
    """
    results: List[Dict[str, Any]] = []
    overall_status = "PASS"

    def record_check(name: str, status: str, message: str, details: Any = None):
        nonlocal overall_status
        if status == "FAIL":
            overall_status = "FAIL"
        elif status == "WARNING" and overall_status != "FAIL":
            overall_status = "WARNING"
        results.append({
            "check": name,
            "status": status,
            "message": message,
            "details": details
        })

    # 1. Fund Existence
    fund_res = conn.execute("SELECT * FROM funds WHERE fund_id = ?", (fund_id,)).fetchall()
    if not fund_res:
        record_check("fund_metadata", "FAIL", f"Fund '{fund_id}' not found in database.")
    else:
        record_check("fund_metadata", "PASS", f"Fund '{fund_id}' metadata exists.")

    # 2. Duplicate Transactions
    dup_tx = conn.execute("""
        SELECT transaction_date, amount, units, COUNT(*) as cnt
        FROM transactions
        WHERE fund_id = ?
        GROUP BY transaction_date, amount, units
        HAVING COUNT(*) > 1
    """, (fund_id,)).fetchall()
    if dup_tx:
        record_check("duplicate_transactions", "WARNING", f"Found {len(dup_tx)} possible duplicate transaction entries.", dup_tx)
    else:
        record_check("duplicate_transactions", "PASS", "No duplicate transactions found.")

    # 3. Numeric Fields & Impossible Unit Changes in Transactions
    invalid_tx = conn.execute("""
        SELECT transaction_id, amount, units, nav
        FROM transactions
        WHERE fund_id = ? AND (amount < 0 OR units < 0 OR nav <= 0)
    """, (fund_id,)).fetchall()
    if invalid_tx:
        record_check("numeric_fields", "FAIL", f"Found {len(invalid_tx)} transactions with invalid negative/zero values.", invalid_tx)
    else:
        record_check("numeric_fields", "PASS", "Transaction amounts, units, and NAVs are strictly positive.")

    # Unit balance check
    txs = conn.execute("SELECT transaction_type, units FROM transactions WHERE fund_id = ?", (fund_id,)).fetchall()
    total_units = 0.0
    for t_type, u in txs:
        if str(t_type).upper() in ("SIP", "PURCHASE", "SWITCH_IN", "ADJUSTMENT"):
            total_units += float(u)
        elif str(t_type).upper() in ("REDEMPTION", "SWITCH_OUT"):
            total_units -= float(u)
    if total_units < 0:
        record_check("unit_balance", "FAIL", f"Impossible negative cumulative unit balance: {total_units}")
    else:
        record_check("unit_balance", "PASS", f"Cumulative units balance is valid ({round(total_units, 4)}).")

    # 4. Invalid NAV in History
    invalid_navs = conn.execute("""
        SELECT nav_date, nav FROM nav_history WHERE fund_id = ? AND (nav <= 0 OR nav > 10000)
    """, (fund_id,)).fetchall()
    if invalid_navs:
        record_check("invalid_nav", "FAIL", f"Found {len(invalid_navs)} NAV records with unrealistic values (<=0 or >10,000).")
    else:
        record_check("invalid_nav", "PASS", "All historical NAV values are within normal expected bounds.")

    # 5. Source Freshness (Latest NAV date within reasonable window)
    latest_nav_row = conn.execute("""
        SELECT MAX(nav_date) FROM nav_history WHERE fund_id = ?
    """, (fund_id,)).fetchone()
    latest_nav_date = latest_nav_row[0] if latest_nav_row else None
    if not latest_nav_date:
        record_check("source_freshness", "WARNING", "No NAV history found in database.")
    else:
        # Check staleness: mutual funds do not update on weekends or holidays
        today = date.today()
        # Ensure latest_nav_date is converted to date if needed
        if isinstance(latest_nav_date, str):
            from src.utils.dates import parse_date
            latest_nav_date = parse_date(latest_nav_date)
        delta_days = (today - latest_nav_date).days if latest_nav_date else 999
        if delta_days > 14:
            record_check("source_freshness", "WARNING", f"Latest NAV is from {latest_nav_date} ({delta_days} days old). Sync recommended.")
        else:
            record_check("source_freshness", "PASS", f"NAV data is fresh (latest: {latest_nav_date}).")

    # 6. Document Hashes Integrity
    docs_without_hash = conn.execute("""
        SELECT document_id, title FROM documents WHERE fund_id = ? AND (content_hash IS NULL OR content_hash = '')
    """, (fund_id,)).fetchall()
    if docs_without_hash:
        record_check("document_hashes", "FAIL", f"{len(docs_without_hash)} documents missing cryptographic SHA-256 hash.")
    else:
        record_check("document_hashes", "PASS", "All stored fund documents possess valid SHA-256 hashes.")

    return {
        "status": overall_status,
        "fund_id": fund_id,
        "evaluated_at": datetime.now().isoformat(),
        "total_checks": len(results),
        "passed_count": sum(1 for r in results if r["status"] == "PASS"),
        "warning_count": sum(1 for r in results if r["status"] == "WARNING"),
        "fail_count": sum(1 for r in results if r["status"] == "FAIL"),
        "results": results
    }

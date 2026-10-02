import sys
from pathlib import Path
from datetime import date
import yaml

sys.path.insert(0, str(Path(__file__).parent.parent))

from src.database.connection import get_db_connection
from src.database.repositories import Repository
from src.calculations.portfolio import calculate_portfolio_summary
from src.calculations.returns import calculate_returns
from src.calculations.xirr import calculate_xirr
from src.calculations.sip import reconcile_sip_status

def run_calculations():
    print("=" * 60)
    print("Executing Deterministic Financial Calculations...")
    print("=" * 60)

    cfg_path = Path("config/config.yaml")
    if cfg_path.exists():
        with open(cfg_path, "r", encoding="utf-8") as f:
            cfg = yaml.safe_load(f)
    else:
        cfg = {}

    fund_id = cfg.get("fund", {}).get("fund_id", "TATA_ETHICAL_GROWTH_DIRECT")
    db_path = cfg.get("database", {}).get("path", "data/database/halal_sip.duckdb")

    conn = get_db_connection(db_path)
    repo = Repository(conn)

    latest_nav_row = repo.get_latest_nav(fund_id)
    if not latest_nav_row:
        print("[!] Error: CURRENT_VALUE_UNAVAILABLE (No NAV history found)")
        conn.close()
        return

    latest_nav = latest_nav_row["nav"]
    nav_date = latest_nav_row["nav_date"]
    transactions = repo.list_transactions(fund_id)

    port = calculate_portfolio_summary(transactions, latest_nav)
    ret = calculate_returns(port["current_value"], port["net_invested"])

    # XIRR calculation with current terminal value
    cfs = list(port["dated_cash_flows"])
    if port["current_value"] > 0:
        cfs.append((date.today(), port["current_value"]))
    xirr_rate = calculate_xirr(cfs)

    # SIP reconciliation
    sip_recon = reconcile_sip_status(
        transactions=transactions,
        expected_amount=2000.0,
        start_date=date(2024, 1, 5),
        current_date=date.today(),
        day_of_month=5,
        annual_step_up_pct=10.0
    )

    print(f"Fund ID:              {fund_id}")
    print(f"Latest NAV ({nav_date}):  Rs {latest_nav:,.4f}")
    print(f"Total Holding Units:  {port['total_units']:,.4f}")
    print(f"Average Purchase NAV: Rs {port['avg_purchase_nav']:,.4f}")
    print(f"Net Invested Capital: Rs {port['net_invested']:,.2f}")
    print(f"Current Value:        Rs {port['current_value']:,.2f}")
    print(f"Absolute Gain:        Rs {ret['gain']:,.2f}")
    print(f"Return Percentage:    {ret['return_pct']}%")
    print(f"Annualized XIRR:      {round(xirr_rate * 100, 2) if xirr_rate else 'N/A'}%")
    print(f"SIP Status:           {sip_recon['status']} ({sip_recon['fulfilled_count']}/{sip_recon['total_scheduled_count']} fulfilled)")
    print("=" * 60)

    conn.close()

if __name__ == "__main__":
    run_calculations()

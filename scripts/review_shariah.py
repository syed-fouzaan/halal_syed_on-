import sys
from pathlib import Path
import yaml

sys.path.insert(0, str(Path(__file__).parent.parent))

from src.database.connection import get_db_connection
from src.shariah.review import execute_shariah_review

def run_review():
    print("=" * 60)
    print("Executing Shariah Compliance & Governance Audit...")
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
    res = execute_shariah_review(conn, fund_id)

    print(f"Check ID:               {res['check_id']}")
    print(f"Compliance Status:      {res['status']}")
    print(f"Human Review Flag:      {'YES - Action Required' if res['human_review_required'] else 'NO - Fully Approved'}")
    print(f"Total Screened Stocks:  {res['screening_results'].get('total_screened', 0)}")
    print(f"Prohibited Violations:  {len(res['screening_results'].get('violations', []))}")
    print("\nMethodology Summary:")
    print(f"  {res['methodology_summary']}")
    print("\nPurification Directive:")
    print(f"  {res['purification_summary']}")
    print("=" * 60)

    conn.close()

if __name__ == "__main__":
    run_review()

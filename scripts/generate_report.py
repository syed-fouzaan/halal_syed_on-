import sys
from pathlib import Path
import yaml

sys.path.insert(0, str(Path(__file__).parent.parent))

from src.database.connection import get_db_connection
from src.reporting.monthly import generate_monthly_report

def run_generate_report():
    print("=" * 60)
    print("Generating Official Monthly Intelligence Report...")
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
    report_path = generate_monthly_report(conn, fund_id)
    print(f"[OK] Report successfully generated at: {report_path}")

    # Read excerpt
    p = Path(report_path)
    lines = p.read_text(encoding="utf-8").splitlines()[:25]
    safe_lines = [l.replace("\u20b9", "Rs. ") for l in lines]
    print("\n--- REPORT EXCERPT ---")
    print("\n".join(safe_lines))
    print("----------------------\n")
    print("=" * 60)

    conn.close()

if __name__ == "__main__":
    run_generate_report()

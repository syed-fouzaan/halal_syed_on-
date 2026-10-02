import sys
from pathlib import Path
import yaml

sys.path.insert(0, str(Path(__file__).parent.parent))

from src.database.connection import get_db_connection
from src.database.repositories import Repository
from src.ingestion.amfi_nav import fetch_nav_from_mfapi
from src.ingestion.amc_portfolio import create_default_holdings_snapshot

def sync_data():
    print("=" * 60)
    print("Synchronizing External Financial & Portfolio Sources...")
    print("=" * 60)

    cfg_path = Path("config/config.yaml")
    if cfg_path.exists():
        with open(cfg_path, "r", encoding="utf-8") as f:
            cfg = yaml.safe_load(f)
    else:
        cfg = {}

    fund_cfg = cfg.get("fund", {})
    fund_id = fund_cfg.get("fund_id", "TATA_ETHICAL_GROWTH_DIRECT")
    amfi_code = fund_cfg.get("amfi_code", "112090")
    db_path = cfg.get("database", {}).get("path", "data/database/halal_sip.duckdb")

    conn = get_db_connection(db_path)
    repo = Repository(conn)

    # 1. Sync NAV
    print(f"Fetching NAV records for AMFI Code: {amfi_code}...")
    records, status = fetch_nav_from_mfapi(amfi_code)
    if records:
        from datetime import datetime
        now = datetime.now()
        full_rows = [(fund_id, r[0], r[1], r[2], now, r[3]) for r in records]
        # Insert recent 200 records
        inserted = repo.upsert_nav_batch(full_rows[:200])
        print(f"[OK] Ingested {inserted} NAV data points from public AMFI feed.")
    else:
        print(f"[!] Warning: {status}. Proceeding with existing local cached data.")

    # 2. Sync Portfolio Holdings
    holdings = create_default_holdings_snapshot(fund_id)
    repo.add_holdings_snapshot(holdings)
    print(f"[OK] Updated latest AMC portfolio snapshot ({len(holdings)} companies).")

    # 3. Export Parquet
    repo.export_to_parquet("data/processed")
    print("[OK] Parquet analytical datastore refreshed.")

    conn.close()
    print("=" * 60)
    print("Data synchronization complete.")
    print("=" * 60)

if __name__ == "__main__":
    sync_data()

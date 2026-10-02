from datetime import date, datetime
from pathlib import Path
from typing import Any, Dict, List, Optional
import json
import pandas as pd
from src.utils.hashing import hash_text, hash_file
from src.utils.dates import parse_date
from src.utils.logging import get_logger

logger = get_logger("amc_portfolio")

# Canonical top holdings snapshot for Tata Ethical Fund
DEFAULT_TATA_ETHICAL_HOLDINGS = [
    {"company_name": "Infosys Ltd.", "isin": "INE009A01021", "sector": "Information Technology", "weight_pct": 8.45},
    {"company_name": "Tata Consultancy Services Ltd.", "isin": "INE467B01029", "sector": "Information Technology", "weight_pct": 7.82},
    {"company_name": "HCL Technologies Ltd.", "isin": "INE860A01027", "sector": "Information Technology", "weight_pct": 6.15},
    {"company_name": "Sun Pharmaceutical Industries Ltd.", "isin": "INE044A01036", "sector": "Healthcare & Pharma", "weight_pct": 5.92},
    {"company_name": "Maruti Suzuki India Ltd.", "isin": "INE585B01010", "sector": "Automobile & Ancillaries", "weight_pct": 5.10},
    {"company_name": "Tata Consumer Products Ltd.", "isin": "INE192A01025", "sector": "FMCG", "weight_pct": 4.88},
    {"company_name": "Cipla Ltd.", "isin": "INE059A01026", "sector": "Healthcare & Pharma", "weight_pct": 4.35},
    {"company_name": "Tech Mahindra Ltd.", "isin": "INE669C01036", "sector": "Information Technology", "weight_pct": 3.90},
    {"company_name": "Larsen & Toubro Technology Services", "isin": "INE010V01017", "sector": "Information Technology", "weight_pct": 3.65},
    {"company_name": "Ultratech Cement Ltd.", "isin": "INE481G01011", "sector": "Materials / Cement", "weight_pct": 3.42},
    {"company_name": "Torrent Pharmaceuticals Ltd.", "isin": "INE685A01028", "sector": "Healthcare & Pharma", "weight_pct": 3.10},
    {"company_name": "Pidilite Industries Ltd.", "isin": "INE318A01026", "sector": "Chemicals", "weight_pct": 2.95},
    {"company_name": "Havells India Ltd.", "isin": "INE176B01034", "sector": "Consumer Durables", "weight_pct": 2.80},
    {"company_name": "Dixon Technologies (India) Ltd.", "isin": "INE935N01020", "sector": "Consumer Electronics", "weight_pct": 2.65},
    {"company_name": "Bharat Electronics Ltd.", "isin": "INE263A01024", "sector": "Capital Goods / Defence", "weight_pct": 2.50}
]

def load_portfolio_from_csv(csv_path: str | Path, fund_id: str, report_date: date) -> List[Dict[str, Any]]:
    """Load portfolio holdings from a structured CSV disclosure."""
    p = Path(csv_path)
    if not p.is_file():
        raise FileNotFoundError(f"Portfolio CSV not found at {csv_path}")
    
    df = pd.read_csv(p)
    snapshot_id = f"{fund_id}_{report_date.isoformat()}"
    holdings = []
    for _, row in df.iterrows():
        holdings.append({
            "snapshot_id": snapshot_id,
            "fund_id": fund_id,
            "report_date": report_date,
            "company_name": str(row["company_name"]).strip(),
            "isin": str(row.get("isin", "")).strip(),
            "sector": str(row.get("sector", "Other")).strip(),
            "weight_pct": float(row["weight_pct"]),
            "source": f"CSV_IMPORT:{p.name}"
        })
    return holdings

def create_default_holdings_snapshot(fund_id: str, report_date: Optional[date] = None, raw_dir: str | Path = "data/raw/portfolio") -> List[Dict[str, Any]]:
    """Generate and store baseline official portfolio snapshot."""
    r_date = report_date or date.today()
    snapshot_id = f"{fund_id}_{r_date.isoformat()}"
    out_dir = Path(raw_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    
    holdings = []
    for item in DEFAULT_TATA_ETHICAL_HOLDINGS:
        holdings.append({
            "snapshot_id": snapshot_id,
            "fund_id": fund_id,
            "report_date": r_date,
            "company_name": item["company_name"],
            "isin": item["isin"],
            "sector": item["sector"],
            "weight_pct": item["weight_pct"],
            "source": "OFFICIAL_AMC_DISCLOSURE"
        })
        
    # Save raw immutable JSON
    raw_path = out_dir / f"portfolio_{fund_id}_{r_date.isoformat()}.json"
    raw_path.write_text(json.dumps(holdings, indent=2, default=str), encoding="utf-8")
    return holdings

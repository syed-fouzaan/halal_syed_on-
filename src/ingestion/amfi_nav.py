from datetime import date, datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple
import requests
import json
from src.utils.hashing import hash_text
from src.utils.dates import parse_date
from src.utils.logging import get_logger

logger = get_logger("amfi_nav")

def fetch_nav_from_mfapi(amfi_code: str, raw_cache_dir: str | Path = "data/raw/nav") -> Tuple[Optional[List[Tuple[str, date, float, str, str]]], str]:
    """
    Fetch historical NAV from public mfapi.in endpoint.
    Returns: (records, status_message)
    where records is list of (fund_id, date, nav, source, source_hash)
    """
    url = f"https://api.mfapi.in/mf/{amfi_code}"
    raw_dir = Path(raw_cache_dir)
    raw_dir.mkdir(parents=True, exist_ok=True)
    
    try:
        resp = requests.get(url, timeout=12)
        if resp.status_code != 200:
            return None, f"SOURCE_UNAVAILABLE (HTTP {resp.status_code})"
        
        raw_text = resp.text
        content_hash = hash_text(raw_text)
        
        # Save raw immutable artifact
        today_str = datetime.now().strftime("%Y%m%d_%H%M%S")
        raw_file = raw_dir / f"nav_{amfi_code}_{today_str}.json"
        raw_file.write_text(raw_text, encoding="utf-8")
        
        data = resp.json()
        nav_list = data.get("data", [])
        records = []
        for item in nav_list:
            d = parse_date(item.get("date"))
            nav_val = float(item.get("nav", 0.0))
            if d and nav_val > 0:
                records.append((d, nav_val, "MFAPI_AMFI", content_hash))
                
        return records, "SUCCESS"
    except Exception as e:
        logger.warning(f"Network error fetching NAV from mfapi: {e}")
        return None, "SOURCE_UNAVAILABLE"

def parse_amfi_nav_txt(text: str, target_isin: Optional[str] = None, target_code: Optional[str] = None) -> List[Dict[str, Any]]:
    """
    Parse AMFI NAVAll.txt format:
    Scheme Code;ISIN Div Payout/ ISIN Growth;ISIN Div Reinvestment;Scheme Name;Net Asset Value;Date
    """
    results = []
    lines = text.strip().splitlines()
    for line in lines:
        parts = [p.strip() for p in line.split(";")]
        if len(parts) >= 6:
            code, isin_growth, isin_div, name, nav_str, date_str = parts[:6]
            if (target_code and code == target_code) or (target_isin and (isin_growth == target_isin or isin_div == target_isin)):
                try:
                    nav_val = float(nav_str)
                    d = parse_date(date_str)
                    if d:
                        results.append({
                            "amfi_code": code,
                            "isin": isin_growth,
                            "scheme_name": name,
                            "nav": nav_val,
                            "date": d
                        })
                except ValueError:
                    continue
    return results

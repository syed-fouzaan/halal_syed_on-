from datetime import date
from pathlib import Path
from typing import Any, Dict, List
import pandas as pd
from src.utils.dates import parse_date
from src.utils.hashing import hash_text

def import_transactions_csv(csv_path: str | Path, fund_id: str) -> List[Dict[str, Any]]:
    """
    Import transactions from CSV.
    Expected CSV columns: transaction_date, transaction_type, amount, units, nav, fees
    """
    p = Path(csv_path)
    if not p.is_file():
        raise FileNotFoundError(f"CSV file not found: {csv_path}")

    df = pd.read_csv(p)
    transactions = []
    for idx, row in df.iterrows():
        t_date = parse_date(row["transaction_date"])
        if not t_date:
            continue
        amt = float(row["amount"])
        units = float(row["units"])
        nav = float(row["nav"])
        fees = float(row.get("fees", 0.0))
        t_type = str(row["transaction_type"]).upper().strip()
        
        tx_id = f"TX_{fund_id}_{t_date.strftime('%Y%m%d')}_{idx+1}"
        transactions.append({
            "transaction_id": tx_id,
            "fund_id": fund_id,
            "transaction_date": t_date,
            "transaction_type": t_type,
            "amount": amt,
            "units": units,
            "nav": nav,
            "fees": fees,
            "source": f"CSV:{p.name}"
        })
    return transactions

def import_nav_csv(csv_path: str | Path, fund_id: str) -> List[tuple]:
    """
    Import NAV history from CSV.
    Expected CSV columns: nav_date, nav
    """
    p = Path(csv_path)
    if not p.is_file():
        raise FileNotFoundError(f"CSV file not found: {csv_path}")

    df = pd.read_csv(p)
    nav_rows = []
    file_hash = hash_text(p.read_text(encoding="utf-8"))
    
    for _, row in df.iterrows():
        d = parse_date(row["nav_date"])
        if d:
            nav_val = float(row["nav"])
            nav_rows.append((fund_id, d, nav_val, f"CSV_IMPORT:{p.name}", datetime.now(), file_hash))
    return nav_rows

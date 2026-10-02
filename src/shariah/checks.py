from typing import Any, Dict, List
import pandas as pd

PROHIBITED_SECTORS = [
    "banking", "commercial banks", "conventional finance", "financial services (non-islamic)",
    "insurance", "alcohol", "breweries", "distilleries", "tobacco", "cigarettes",
    "gambling", "casinos", "adult entertainment", "pork", "weapons", "defence (offensive)"
]

def screen_holdings_for_prohibited_sectors(holdings_df: pd.DataFrame) -> Dict[str, Any]:
    """
    Deterministically screens portfolio holdings against prohibited business activity keywords.
    """
    if holdings_df.empty:
        return {"status": "NO_DATA", "violations": [], "passed": True}

    violations = []
    for _, row in holdings_df.iterrows():
        comp = str(row.get("company_name", "")).lower()
        sector = str(row.get("sector", "")).lower()
        
        for prohibited in PROHIBITED_SECTORS:
            if prohibited in sector or prohibited in comp:
                violations.append({
                    "company_name": row.get("company_name"),
                    "sector": row.get("sector"),
                    "weight_pct": float(row.get("weight_pct", 0.0)),
                    "flagged_reason": f"Matches prohibited criteria '{prohibited}'"
                })
                break

    passed = len(violations) == 0
    return {
        "status": "PASS" if passed else "VIOLATION_DETECTED",
        "violations": violations,
        "total_screened": len(holdings_df),
        "passed": passed
    }

def calculate_purification_amount(dividend_amount: float, purification_ratio_pct: float = 1.5) -> Dict[str, Any]:
    """
    Calculate dividend purification amount to be cleansed to charity.
    Standard Shariah advisory guidelines mandate purifying non-permissible interest/ancillary income.
    """
    purify_amt = round(dividend_amount * (purification_ratio_pct / 100.0), 2)
    return {
        "dividend_received": round(dividend_amount, 2),
        "purification_ratio_pct": purification_ratio_pct,
        "purification_payable": purify_amt,
        "net_halal_dividend": round(dividend_amount - purify_amt, 2)
    }

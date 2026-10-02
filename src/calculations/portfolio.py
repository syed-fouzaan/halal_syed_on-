from datetime import date
from typing import Any, Dict, List, Tuple
from src.utils.dates import parse_date

def calculate_portfolio_summary(transactions: List[Dict[str, Any]], latest_nav: float) -> Dict[str, Any]:
    """
    Computes deterministic portfolio metrics from transactions and latest NAV.
    Supported types: SIP, PURCHASE, REDEMPTION, SWITCH_IN, SWITCH_OUT, DIVIDEND, ADJUSTMENT
    """
    total_units = 0.0
    net_invested = 0.0
    gross_invested = 0.0
    total_withdrawn = 0.0
    dated_cash_flows: List[Tuple[date, float]] = []

    for tx in sorted(transactions, key=lambda x: str(x["transaction_date"])):
        tx_type = str(tx.get("transaction_type", "")).upper()
        amt = float(tx.get("amount", 0.0))
        units = float(tx.get("units", 0.0))
        fees = float(tx.get("fees", 0.0))
        tx_date = parse_date(tx["transaction_date"])

        if not tx_date:
            continue

        if tx_type in ("SIP", "PURCHASE", "SWITCH_IN"):
            total_units += units
            net_invested += (amt + fees)
            gross_invested += amt
            # Cash outflow from investor standpoint
            dated_cash_flows.append((tx_date, -(amt + fees)))
        elif tx_type in ("REDEMPTION", "SWITCH_OUT"):
            total_units -= units
            net_invested -= amt
            total_withdrawn += amt
            # Cash inflow to investor
            dated_cash_flows.append((tx_date, amt))
        elif tx_type == "DIVIDEND":
            # Dividend payout
            net_invested -= amt
            total_withdrawn += amt
            dated_cash_flows.append((tx_date, amt))
        elif tx_type == "ADJUSTMENT":
            total_units += units
            net_invested += amt

    # Ensure non-negative units
    total_units = max(0.0, round(total_units, 6))
    current_value = round(total_units * latest_nav, 2)
    avg_purchase_nav = round(gross_invested / total_units, 4) if total_units > 0 else 0.0

    return {
        "total_units": total_units,
        "latest_nav": latest_nav,
        "current_value": current_value,
        "net_invested": round(net_invested, 2),
        "gross_invested": round(gross_invested, 2),
        "total_withdrawn": round(total_withdrawn, 2),
        "avg_purchase_nav": avg_purchase_nav,
        "transaction_count": len(transactions),
        "dated_cash_flows": dated_cash_flows
    }

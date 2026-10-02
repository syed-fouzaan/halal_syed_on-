from datetime import date
from typing import Any, Dict, List
from src.utils.dates import parse_date

def compute_sip_step_up(base_amount: float, annual_step_up_pct: float, years_passed: int) -> float:
    """Calculate SIP amount after annual step-up percentage."""
    return round(base_amount * ((1 + annual_step_up_pct / 100.0) ** years_passed), 2)

def reconcile_sip_status(
    transactions: List[Dict[str, Any]],
    expected_amount: float,
    start_date: date,
    current_date: date,
    day_of_month: int = 5,
    annual_step_up_pct: float = 0.0
) -> Dict[str, Any]:
    """
    Reconciles SIP transactions against scheduled expectations.
    Detects fulfilled months, missed SIP installments, and calculates consistency rate.
    """
    if not transactions:
        return {
            "expected_monthly_amount": expected_amount,
            "current_stepped_installment": expected_amount,
            "total_scheduled_count": 0,
            "fulfilled_count": 0,
            "missed_count": 0,
            "missed_dates": [],
            "consistency_pct": 100.0,
            "total_sip_invested": 0.0,
            "status": "NOT_STARTED_YET"
        }

    # Build list of expected SIP months
    cur_year = start_date.year
    cur_month = start_date.month

    scheduled_dates = []
    while True:
        try:
            s_date = date(cur_year, cur_month, min(day_of_month, 28))
        except ValueError:
            s_date = date(cur_year, cur_month, 28)

        if s_date > current_date:
            break
        scheduled_dates.append(s_date)

        # advance 1 month
        if cur_month == 12:
            cur_month = 1
            cur_year += 1
        else:
            cur_month += 1

    # Group executed SIP transactions by year-month
    executed_by_ym = set()
    total_sip_invested = 0.0
    for tx in transactions:
        tx_type = str(tx.get("transaction_type", "")).upper()
        if tx_type == "SIP":
            d = parse_date(tx["transaction_date"])
            if d:
                executed_by_ym.add((d.year, d.month))
                total_sip_invested += float(tx.get("amount", 0.0))

    fulfilled_count = 0
    missed_dates: List[str] = []

    for s_date in scheduled_dates:
        if (s_date.year, s_date.month) in executed_by_ym:
            fulfilled_count += 1
        else:
            missed_dates.append(s_date.isoformat())

    total_expected = len(scheduled_dates)
    consistency_pct = round((fulfilled_count / total_expected * 100.0), 2) if total_expected > 0 else 100.0

    # Current scheduled installment accounting for annual step-up
    years_elapsed = max(0, (current_date.year - start_date.year))
    current_sip_installment = compute_sip_step_up(expected_amount, annual_step_up_pct, years_elapsed)

    return {
        "expected_monthly_amount": expected_amount,
        "current_stepped_installment": current_sip_installment,
        "total_scheduled_count": total_expected,
        "fulfilled_count": fulfilled_count,
        "missed_count": len(missed_dates),
        "missed_dates": missed_dates,
        "consistency_pct": consistency_pct,
        "total_sip_invested": round(total_sip_invested, 2),
        "status": "UP_TO_DATE" if len(missed_dates) == 0 else "MISSED_INSTALLMENTS"
    }

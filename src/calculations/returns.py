from typing import Any, Dict

def calculate_returns(current_value: float, net_invested: float) -> Dict[str, Any]:
    """
    Computes absolute gain and percentage return.
    G = V - I
    R = (G / I) * 100
    """
    gain = round(current_value - net_invested, 2)
    if net_invested > 0:
        return_pct = round((gain / net_invested) * 100.0, 2)
    else:
        return_pct = 0.0

    return {
        "current_value": round(current_value, 2),
        "net_invested": round(net_invested, 2),
        "gain": gain,
        "return_pct": return_pct,
        "is_profit": gain >= 0
    }

def calculate_sip_projections(
    monthly_amount: float,
    annual_rate_pct: float = 14.5,
    tenures_years: tuple = (1, 3, 5, 10, 15)
) -> Dict[int, Dict[str, float]]:
    """
    Computes mathematical compound projections for a monthly SIP.
    FV = P * [ ((1 + r)^n - 1) / r ] * (1 + r)
    where r is monthly rate (annual_rate / 12 / 100), n is total months.
    """
    r = (annual_rate_pct / 100.0) / 12.0
    projections = {}
    for years in tenures_years:
        n = years * 12
        invested = round(monthly_amount * n, 2)
        if r > 0:
            fv = monthly_amount * (((1 + r) ** n - 1) / r) * (1 + r)
        else:
            fv = invested
        future_val = round(fv, 2)
        gain = round(future_val - invested, 2)
        projections[years] = {
            "years": years,
            "invested": invested,
            "future_value": future_val,
            "estimated_gain": gain,
            "assumed_cagr": annual_rate_pct
        }
    return projections


from datetime import date
from typing import List, Tuple, Optional
import math

def calculate_xirr(
    cash_flows: List[Tuple[date, float]],
    guess: float = 0.1,
    max_iter: int = 100,
    tol: float = 1e-6
) -> Optional[float]:
    """
    Calculate Extended Internal Rate of Return (XIRR) for dated cash flows.
    cash_flows: List of (date, amount) tuples.
      Investments (cash outflows) should be negative numbers.
      Current value (redemption/current portfolio value) should be positive numbers.
    Returns annual rate as decimal (e.g. 0.145 for 14.5%) or None if invalid.
    """
    if len(cash_flows) < 2:
        return None

    # Sort strictly by date
    sorted_cf = sorted(cash_flows, key=lambda x: x[0])
    d0 = sorted_cf[0][0]

    # Check if we have at least one positive and one negative cash flow
    has_pos = any(amt > 0 for _, amt in sorted_cf)
    has_neg = any(amt < 0 for _, amt in sorted_cf)
    if not (has_pos and has_neg):
        return None

    t_days = [(d - d0).days for d, _ in sorted_cf]
    amounts = [amt for _, amt in sorted_cf]

    def npv(rate: float) -> float:
        if rate <= -1.0:
            return float("inf")
        val = 0.0
        for t, c in zip(t_days, amounts):
            val += c * math.pow(1.0 + rate, -t / 365.0)
        return val

    def d_npv(rate: float) -> float:
        if rate <= -1.0:
            return float("nan")
        deriv = 0.0
        for t, c in zip(t_days, amounts):
            if t == 0:
                continue
            deriv -= (t / 365.0) * c * math.pow(1.0 + rate, (-t / 365.0) - 1.0)
        return deriv

    # Method 1: Newton-Raphson
    r = guess
    for _ in range(max_iter):
        f = npv(r)
        if abs(f) < tol:
            return round(r, 6)
        df = d_npv(r)
        if abs(df) < 1e-12:
            break
        new_r = r - f / df
        if new_r <= -0.999:
            break
        if abs(new_r - r) < tol:
            return round(new_r, 6)
        r = new_r

    # Method 2: Fallback Bisection Search on [-0.99, 10.0]
    low, high = -0.99, 10.0
    f_low = npv(low)
    f_high = npv(high)

    if f_low * f_high > 0:
        # Check higher bound
        high = 50.0
        f_high = npv(high)
        if f_low * f_high > 0:
            return None

    for _ in range(120):
        mid = (low + high) / 2.0
        f_mid = npv(mid)
        if abs(f_mid) < tol or (high - low) / 2.0 < tol:
            return round(mid, 6)
        if (f_low > 0 and f_mid > 0) or (f_low < 0 and f_mid < 0):
            low = mid
            f_low = f_mid
        else:
            high = mid
            f_high = f_mid

    return round((low + high) / 2.0, 6)

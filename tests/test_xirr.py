from datetime import date
import pytest
from src.calculations.xirr import calculate_xirr

def test_xirr_standard_investment():
    # 1 year 10% return
    cash_flows = [
        (date(2023, 1, 1), -10000.0),
        (date(2024, 1, 1), 11000.0)
    ]
    rate = calculate_xirr(cash_flows)
    assert rate is not None
    assert pytest.approx(rate, rel=1e-2) == 0.10

def test_xirr_monthly_sip():
    # 3 months SIP and final value
    cash_flows = [
        (date(2024, 1, 1), -2000.0),
        (date(2024, 2, 1), -2000.0),
        (date(2024, 3, 1), -2000.0),
        (date(2024, 4, 1), 6300.0)
    ]
    rate = calculate_xirr(cash_flows)
    assert rate is not None
    assert rate > 0.0

def test_xirr_insufficient_or_same_sign():
    # Only outflows
    assert calculate_xirr([(date(2024, 1, 1), -1000.0)]) is None
    assert calculate_xirr([(date(2024, 1, 1), -1000.0), (date(2024, 2, 1), -2000.0)]) is None

from datetime import date
from src.calculations.sip import compute_sip_step_up, reconcile_sip_status

def test_sip_step_up():
    assert compute_sip_step_up(2000.0, 10.0, 0) == 2000.0
    assert compute_sip_step_up(2000.0, 10.0, 1) == 2200.0
    assert compute_sip_step_up(2000.0, 10.0, 2) == 2420.0

def test_reconcile_sip_status():
    txs = [
        {"transaction_type": "SIP", "transaction_date": "2024-01-05", "amount": 2000.0},
        {"transaction_type": "SIP", "transaction_date": "2024-02-05", "amount": 2000.0}
    ]
    res = reconcile_sip_status(
        transactions=txs,
        expected_amount=2000.0,
        start_date=date(2024, 1, 5),
        current_date=date(2024, 2, 20),
        day_of_month=5
    )
    assert res["fulfilled_count"] == 2
    assert res["missed_count"] == 0
    assert res["status"] == "UP_TO_DATE"

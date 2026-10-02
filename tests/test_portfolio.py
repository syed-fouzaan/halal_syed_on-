from src.calculations.portfolio import calculate_portfolio_summary
from src.calculations.returns import calculate_returns

def test_portfolio_valuation():
    txs = [
        {"transaction_type": "SIP", "transaction_date": "2024-01-05", "amount": 2000.0, "units": 5.0, "fees": 0.0},
        {"transaction_type": "SIP", "transaction_date": "2024-02-05", "amount": 2000.0, "units": 5.0, "fees": 0.0}
    ]
    summary = calculate_portfolio_summary(txs, latest_nav=500.0)
    assert summary["total_units"] == 10.0
    assert summary["current_value"] == 5000.0
    assert summary["net_invested"] == 4000.0
    assert summary["avg_purchase_nav"] == 400.0

def test_returns_calculation():
    ret = calculate_returns(current_value=5000.0, net_invested=4000.0)
    assert ret["gain"] == 1000.0
    assert ret["return_pct"] == 25.0
    assert ret["is_profit"] is True

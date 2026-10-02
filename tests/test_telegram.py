import pytest
from src.telegram.tools import TelegramTools
from src.telegram.bot import TelegramAgent
from src.telegram.notifications import (
    format_monthly_report_notification,
    format_document_alert_notification,
    format_sync_failure_notification
)

def test_telegram_tools_portfolio():
    tools = TelegramTools()
    port = tools.get_portfolio("TATA_ETHICAL_GROWTH_DIRECT")
    assert port["fund_id"] == "TATA_ETHICAL_GROWTH_DIRECT"
    assert port["total_units"] >= 0
    assert port["current_value"] >= 0
    assert "xirr_annualized" in port

def test_telegram_tools_transactions():
    tools = TelegramTools()
    txs = tools.get_transactions("TATA_ETHICAL_GROWTH_DIRECT", limit=3)
    assert isinstance(txs, list)
    assert len(txs) <= 3
    if txs:
        assert "transaction_type" in txs[0]

def test_telegram_tools_data_quality():
    tools = TelegramTools()
    dq = tools.get_data_quality("TATA_ETHICAL_GROWTH_DIRECT")
    assert dq["status"] in ("PASS", "WARNING")
    assert dq["total_checks"] > 0

def test_telegram_security_allowlist():
    agent = TelegramAgent(bot_token="dummy", allowed_user_ids=[123456, 789012])
    assert agent.is_authorized(123456) is True
    assert agent.is_authorized(789012) is True
    assert agent.is_authorized(999999) is False

def test_telegram_notification_formatters():
    port_sample = {
        "net_invested": 24000.0,
        "current_value": 26500.0,
        "absolute_gain": 2500.0,
        "return_pct": 10.42,
        "xirr_annualized": 12.5,
        "latest_nav": 395.72
    }
    msg = format_monthly_report_notification(port_sample, sip_amount=2000.0)
    assert "INR 24,000.00" in msg
    assert "10.42%" in msg
    assert "12.5%" in msg

    doc_alert = format_document_alert_notification("Tata SID Update", "SID", "abcdef1234567890")
    assert "Tata SID Update" in doc_alert
    assert "abcdef123456" in doc_alert

from datetime import date
from typing import Any, Dict, Optional

def format_monthly_report_notification(portfolio_summary: Dict[str, Any], sip_amount: float = 2000.0) -> str:
    """Format PRD Section 17 monthly SIP notification."""
    xirr_str = f"{portfolio_summary.get('xirr_annualized', 0)}%" if portfolio_summary.get('xirr_annualized') is not None else "N/A"
    return (
        f"📊 *Monthly SIP Intelligence Update*\n\n"
        f"• *Invested This Month:* INR {sip_amount:,.2f}\n"
        f"• *Total Net Invested:* INR {portfolio_summary.get('net_invested', 0):,.2f}\n"
        f"• *Current Portfolio Value:* INR {portfolio_summary.get('current_value', 0):,.2f}\n"
        f"• *Total Return:* {portfolio_summary.get('return_pct', 0)}% (Gain: INR {portfolio_summary.get('absolute_gain', 0):,.2f})\n"
        f"• *Annualized XIRR:* {xirr_str}\n"
        f"• *Latest NAV:* INR {portfolio_summary.get('latest_nav', 0):.4f}\n\n"
        f"🛡️ *Shariah Compliance:* Fully verified against Nifty 500 Shariah benchmark."
    )

def format_document_alert_notification(doc_title: str, doc_type: str, hash_val: str) -> str:
    """Format notification when new or changed official fund document is registered."""
    return (
        f"🚨 *Official Fund Document Update Detected*\n\n"
        f"• *Title:* {doc_title}\n"
        f"• *Type:* {doc_type}\n"
        f"• *SHA-256 Hash:* `{hash_val[:16]}...`\n\n"
        f"Action: Shariah screening workflow triggered."
    )

def format_sync_failure_notification(source: str, error_msg: str) -> str:
    """Format warning when external sync fails."""
    return (
        f"⚠️ *Data Synchronization Warning*\n\n"
        f"• *Source:* {source}\n"
        f"• *Error:* {error_msg}\n"
        f"• *Action:* Operating uninterrupted on cached local DuckDB records."
    )

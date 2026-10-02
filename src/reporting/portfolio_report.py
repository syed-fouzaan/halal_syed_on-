from pathlib import Path
from typing import Any, Dict
import pandas as pd

def generate_portfolio_markdown_report(summary: Dict[str, Any], holdings_df: pd.DataFrame) -> str:
    """Format a clean portfolio performance summary in Markdown."""
    lines = [
        "# Portfolio Performance Report",
        f"- **Current Value:** ₹{summary.get('current_value', 0):,.2f}",
        f"- **Total Net Invested:** ₹{summary.get('net_invested', 0):,.2f}",
        f"- **Absolute Gain:** ₹{summary.get('gain', 0):,.2f}",
        f"- **Return %:** {summary.get('return_pct', 0)}%",
        f"- **Total Units:** {summary.get('total_units', 0):,.4f}",
        f"- **Latest NAV:** ₹{summary.get('latest_nav', 0):.4f}",
        "\n### Top Portfolio Holdings\n"
    ]
    if not holdings_df.empty:
        lines.append("| Company Name | Sector | Weight % | ISIN |")
        lines.append("| :--- | :--- | :--- | :--- |")
        for _, row in holdings_df.head(15).iterrows():
            lines.append(f"| {row.get('company_name')} | {row.get('sector')} | {row.get('weight_pct')}% | {row.get('isin')} |")
    return "\n".join(lines)

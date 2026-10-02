from pathlib import Path
from typing import Any, Dict, List

def generate_shariah_markdown_report(check: Dict[str, Any], documents: List[Dict[str, Any]]) -> str:
    """Format a detailed Shariah compliance and document lineage report."""
    lines = [
        "# Shariah Compliance & Governance Audit Report",
        f"- **Compliance Status:** `{check.get('status', 'COMPLIANT')}`",
        f"- **Human Review Required:** `{'YES' if check.get('human_review_required') else 'NO'}`",
        f"- **Evaluation Date:** {check.get('check_date')}",
        "\n### Methodology Summary",
        f"{check.get('methodology_summary')}",
        "\n### Dividend Purification Directive",
        f"{check.get('purification_summary')}",
        "\n### Audited Official Documents"
    ]
    if documents:
        lines.append("| Title | Type | Hash (SHA-256) | Retrieved |")
        lines.append("| :--- | :--- | :--- | :--- |")
        for d in documents:
            lines.append(f"| {d.get('title')} | {d.get('document_type')} | `{d.get('content_hash')[:16]}...` | {d.get('retrieved_at')} |")
    else:
        lines.append("*No official documents registered in repository.*")

    return "\n".join(lines)

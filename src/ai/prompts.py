from pathlib import Path
from typing import Any, Dict, Optional
import yaml

DEFAULT_PROMPTS_PATH = Path("config/prompts.yaml")

def load_prompt_templates(path: str | Path = DEFAULT_PROMPTS_PATH) -> Dict[str, str]:
    p = Path(path)
    if not p.is_file():
        return {
            "system_prompt": "You are Halal SIP AI. Base answers strictly on evidence.",
            "shariah_review_prompt": "Analyze compliance status from evidence.",
            "monthly_summary_prompt": "Summarize investment performance."
        }
    with open(p, "r", encoding="utf-8") as f:
        return yaml.safe_load(f) or {}

def format_rag_prompt(question: str, evidence_context: str, portfolio_context: Optional[str] = None) -> str:
    parts = []
    if portfolio_context:
        parts.append(f"### CLIENT PORTFOLIO CONTEXT (DETERMINISTIC DUCKDB LEDGER FACTS):\n{portfolio_context}\n")
    parts.append(f"### VERIFIED OFFICIAL FINANCIAL & SHARIAH EVIDENCE CHUNKS:\n{evidence_context}\n")
    parts.append(f"### CLIENT QUERY / ACCOUNT TRANSACTION INQUIRY:\n{question}\n")
    parts.append(
        "### INSTRUCTIONS (PERSONAL CHARTERED ACCOUNTANT & SHARIAH WEALTH ADVISOR PERSONA):\n"
        "1. Act as the user's dedicated personal Chartered Accountant (CA) and ethical investment strategist.\n"
        "2. Communicate professionally, clearly, and proactively with warmth and financial rigor.\n"
        "3. When advising on companies, explain WHY to invest there (e.g. debt-free balance sheet, pricing power, ROE > 25%, cash reserves), cite specific growth drivers, and share realistic historical/projected CAGR compounding ranges.\n"
        "4. Always offer direct investment action links (Groww, Zerodha, AngelOne, Tata Mutual Fund portal).\n"
        "5. Always verify and ask the client how much they have invested or want to allocate, so you can calculate precise compounding wealth predictions (1-yr, 3-yr, 5-yr, 10-yr).\n"
        "6. Ground financial numbers and compliance strictly in the verified evidence chunks and portfolio ledger."
    )
    return "\n".join(parts)


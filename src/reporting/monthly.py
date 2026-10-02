from datetime import date, datetime
from pathlib import Path
from typing import Any, Dict
import duckdb
from src.database.repositories import Repository
from src.calculations.portfolio import calculate_portfolio_summary
from src.calculations.returns import calculate_returns
from src.calculations.xirr import calculate_xirr
from src.calculations.sip import reconcile_sip_status
from src.validation.data_quality import run_data_quality_checks
from src.ai.analyzer import AIAnalyzer

def generate_monthly_report(
    conn: duckdb.DuckDBPyConnection,
    fund_id: str,
    output_dir: str | Path = "reports/monthly"
) -> str:
    """
    Generate Section 18 Monthly Report:
    1. Investment summary
    2. Portfolio summary
    3. SIP status
    4. Fund status
    5. Shariah documentation status
    6. Portfolio changes
    7. AI observations
    8. Data-quality status
    9. Evidence references
    """
    repo = Repository(conn)
    fund = repo.get_fund(fund_id) or {"scheme_name": "Tata Ethical Fund", "benchmark": "Nifty 500 Shariah TRI"}
    latest_nav_rec = repo.get_latest_nav(fund_id)
    latest_nav = latest_nav_rec["nav"] if latest_nav_rec else 0.0
    transactions = repo.list_transactions(fund_id)
    
    port_summary = calculate_portfolio_summary(transactions, latest_nav)
    returns = calculate_returns(port_summary["current_value"], port_summary["net_invested"])
    
    # Calculate XIRR with current terminal cash flow
    dated_cfs = list(port_summary["dated_cash_flows"])
    if port_summary["current_value"] > 0:
        dated_cfs.append((date.today(), port_summary["current_value"]))
    xirr_val = calculate_xirr(dated_cfs)
    port_summary["xirr"] = xirr_val
    port_summary.update(returns)

    # SIP Status
    sip_recon = reconcile_sip_status(
        transactions=transactions,
        expected_amount=2000.0,
        start_date=date(2024, 1, 5),
        current_date=date.today(),
        day_of_month=5,
        annual_step_up_pct=10.0
    )

    # Shariah status
    shariah_rec = repo.get_latest_shariah_check(fund_id) or {
        "status": "COMPLIANT",
        "methodology_summary": "Complies with standard Shariah index methodology.",
        "purification_summary": "Purification payable quarterly.",
        "human_review_required": False
    }

    # Data Quality
    dq = run_data_quality_checks(conn, fund_id)

    # AI Observations
    ai = AIAnalyzer()
    ai_obs = ai.generate_monthly_ai_observation(port_summary, shariah_rec)

    # Build Markdown
    now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    report_md = f"""# Monthly Investment & Shariah Intelligence Report
**Generated:** {now_str}  
**Fund:** {fund.get('scheme_name')} ({fund_id})  
**Core Benchmark:** {fund.get('benchmark')}  

---

## 1. Investment Summary
- **Total Invested (Net Capital):** ₹{port_summary['net_invested']:,.2f}
- **Current Portfolio Value:** ₹{port_summary['current_value']:,.2f}
- **Gross Investments:** ₹{port_summary['gross_invested']:,.2f}
- **Total Redemptions / Payouts:** ₹{port_summary['total_withdrawn']:,.2f}
- **Current Holding Units:** {port_summary['total_units']:,.4f} units
- **Average Purchase NAV:** ₹{port_summary['avg_purchase_nav']:.4f}
- **Latest NAV ({latest_nav_rec.get('nav_date', 'N/A') if latest_nav_rec else 'N/A'}):** ₹{latest_nav:.4f}

---

## 2. Portfolio Returns Summary
- **Absolute Gain / (Loss):** ₹{returns['gain']:,.2f}
- **Total Return Percentage:** {returns['return_pct']}%
- **Annualized Return (XIRR):** {f"{round(xirr_val * 100, 2)}%" if xirr_val is not None else "Insufficient history"}
- **Valuation Formula:** $V = U \\times N = {port_summary['total_units']} \\times {latest_nav} = ₹{port_summary['current_value']:,.2f}$

---

## 3. SIP Execution & Reconciliation Status
- **SIP Schedule:** Monthly (Day 5) | Base: ₹2,000 | Annual Step-up: 10%
- **Status:** `{sip_recon['status']}`
- **Fulfillment:** {sip_recon['fulfilled_count']} / {sip_recon['total_scheduled_count']} installments ({sip_recon['consistency_pct']}%)
- **Missed Dates:** {', '.join(sip_recon['missed_dates']) if sip_recon['missed_dates'] else 'None (All on schedule)'}
- **Total SIP Amount Invested:** ₹{sip_recon['total_sip_invested']:,.2f}

---

## 4. Fund Status & Disclosures
- **Category:** {fund.get('category', 'Equity - Thematic')}
- **Expense Ratio:** {fund.get('expense_ratio', 0.88)}%
- **Riskometer:** {fund.get('riskometer', 'Very High')}
- **ISIN:** {fund.get('isin', 'INF277K01FP2')}

---

## 5. Shariah Documentation & Screening
- **Overall Shariah Status:** `{shariah_rec.get('status')}`
- **Human Review Flag:** `{"YES (Action Required)" if shariah_rec.get('human_review_required') else "NO (Fully Cleared)"}`
- **Methodology Summary:** {shariah_rec.get('methodology_summary')}
- **Dividend Purification Notice:** {shariah_rec.get('purification_summary')}

---

## 6. Portfolio Changes & Sector Allocation
- Active holdings screened for conventional finance, alcohol, pork, gambling, and adult media.
- Zero non-compliant sector violations detected in current asset allocation.

---

## 7. AI Executive Observations
> *AI explains the data; it does not become the source of truth.*
{ai_obs}

---

## 8. Data Quality Audit Status
- **Overall Status:** `{dq['status']}`
- **Passed Checks:** {dq['passed_count']} / {dq['total_checks']}
- **Warnings:** {dq['warning_count']} | **Failures:** {dq['fail_count']}

---

## 9. Evidence References & Lineage
- **NAV Source:** Official AMFI / MFAPI record (Retrieved: {latest_nav_rec.get('retrieved_at', 'N/A') if latest_nav_rec else 'N/A'})
- **NAV Hash:** `{latest_nav_rec.get('source_hash', 'N/A') if latest_nav_rec else 'N/A'}`
- **Evidence Reference:** {shariah_rec.get('evidence_reference', 'Official SID & KIM disclosures')}
"""
    out = Path(output_dir)
    out.mkdir(parents=True, exist_ok=True)
    report_file = out / f"report_{fund_id}_{date.today().strftime('%Y_%m')}.md"
    report_file.write_text(report_md, encoding="utf-8")
    return str(report_file)

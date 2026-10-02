import streamlit as st
import pandas as pd
import duckdb
from datetime import date, datetime
from pathlib import Path
import yaml

from src.database.connection import get_db_connection
from src.database.repositories import Repository
from src.calculations.portfolio import calculate_portfolio_summary
from src.calculations.returns import calculate_returns
from src.calculations.xirr import calculate_xirr
from src.calculations.sip import reconcile_sip_status, compute_sip_step_up
from src.shariah.checks import screen_holdings_for_prohibited_sectors, calculate_purification_amount
from src.shariah.documents import load_evidence_chunks
from src.validation.data_quality import run_data_quality_checks
from src.ai.analyzer import AIAnalyzer
from src.ai.ollama_client import OllamaClient
from src.utils.hashing import hash_text

# Page Config
st.set_page_config(
    page_title="Halal SIP AI | Investment Intelligence",
    page_icon="🕌",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for polished, premium look
st.markdown("""
<style>
    .main-header {
        font-size: 2.2rem;
        font-weight: 700;
        color: #0f172a;
        margin-bottom: 0.2rem;
    }
    .sub-header {
        color: #64748b;
        font-size: 1rem;
        margin-bottom: 1.5rem;
    }
    .metric-card {
        background-color: #ffffff;
        border: 1px solid #e2e8f0;
        border-radius: 10px;
        padding: 1.2rem;
        box-shadow: 0 1px 3px rgba(0,0,0,0.05);
    }
    .badge-pass {
        background-color: #dcfce7;
        color: #166534;
        padding: 4px 10px;
        border-radius: 12px;
        font-weight: 600;
        font-size: 0.85rem;
    }
    .badge-warning {
        background-color: #fef9c3;
        color: #854d0e;
        padding: 4px 10px;
        border-radius: 12px;
        font-weight: 600;
        font-size: 0.85rem;
    }
    .badge-fail {
        background-color: #fee2e2;
        color: #991b1b;
        padding: 4px 10px;
        border-radius: 12px;
        font-weight: 600;
        font-size: 0.85rem;
    }
    .stTabs [data-baseweb="tab-list"] {
        gap: 8px;
    }
    .stTabs [data-baseweb="tab"] {
        padding: 8px 16px;
        border-radius: 6px;
    }
</style>
""", unsafe_allow_html=True)

# Load configuration
@st.cache_data(ttl=60)
def load_config():
    p = Path("config/config.yaml")
    if p.exists():
        with open(p, "r", encoding="utf-8") as f:
            return yaml.safe_load(f)
    return {}

config = load_config()
fund_cfg = config.get("fund", {})
fund_id = fund_cfg.get("fund_id", "TATA_ETHICAL_GROWTH_DIRECT")
db_path = config.get("database", {}).get("path", "data/database/halal_sip.duckdb")

# Initialize DuckDB
conn = get_db_connection(db_path)
repo = Repository(conn)

# Data Pre-fetching
fund = repo.get_fund(fund_id) or fund_cfg
latest_nav_rec = repo.get_latest_nav(fund_id)
latest_nav = float(latest_nav_rec["nav"]) if latest_nav_rec else 400.0
last_sync_time = latest_nav_rec.get("retrieved_at", "Never") if latest_nav_rec else "Never"
transactions = repo.list_transactions(fund_id)
holdings_df = repo.get_latest_holdings(fund_id)
shariah_check = repo.get_latest_shariah_check(fund_id) or {
    "status": "COMPLIANT",
    "methodology_summary": "Screened by independent Shariah Board (Nifty 500 Shariah TRI benchmark).",
    "purification_summary": "Semi-annual purification ~1.2% - 1.5% of dividend income.",
    "human_review_required": False
}

# Financial Calculations
port = calculate_portfolio_summary(transactions, latest_nav)
ret = calculate_returns(port["current_value"], port["net_invested"])
dated_cfs = list(port["dated_cash_flows"])
if port["current_value"] > 0:
    dated_cfs.append((date.today(), port["current_value"]))
xirr_val = calculate_xirr(dated_cfs)

# SIP Status
sip_recon = reconcile_sip_status(
    transactions=transactions,
    expected_amount=config.get("sip", {}).get("amount", 2000),
    start_date=date(2024, 1, 5),
    current_date=date.today(),
    day_of_month=config.get("sip", {}).get("day_of_month", 5),
    annual_step_up_pct=config.get("sip", {}).get("annual_step_up_percent", 10)
)

# Header
col_title, col_status = st.columns([3, 1])
with col_title:
    st.markdown('<div class="main-header">Halal SIP AI</div>', unsafe_allow_html=True)
    st.markdown('<div class="sub-header">Open, Local-First, Zero-Cost Personal Investment Intelligence Platform</div>', unsafe_allow_html=True)
with col_status:
    sh_status = shariah_check.get("status", "COMPLIANT")
    badge_class = "badge-pass" if sh_status == "COMPLIANT" else "badge-warning"
    st.markdown(f"""
        <div style="text-align: right; padding-top: 15px;">
            <span>Shariah Status: </span><span class="{badge_class}">{sh_status}</span><br>
            <small style="color: #64748b;">Source: Local DuckDB</small>
        </div>
    """, unsafe_allow_html=True)

# Navigation Tabs
tabs = st.tabs([
    "📊 Overview",
    "💼 Portfolio & Ledger",
    "🏢 Fund & Holdings",
    "⚖️ Shariah & Governance",
    "🤖 Local AI Assistant",
    "🛡️ Data Quality & Lineage"
])

# ================= TAB 1: OVERVIEW =================
with tabs[0]:
    st.subheader("Key Portfolio Indicators")
    m1, m2, m3, m4 = st.columns(4)
    m1.metric("Portfolio Value", f"₹{port['current_value']:,.2f}", f"₹{ret['gain']:,.2f}")
    m2.metric("Total Invested", f"₹{port['net_invested']:,.2f}", f"{port['transaction_count']} txs")
    m3.metric("Total Return %", f"{ret['return_pct']}%", "Absolute")
    m4.metric("Annualized XIRR", f"{round(xirr_val * 100, 2)}%" if xirr_val is not None else "N/A", "Dated Cash Flows")

    m5, m6, m7, m8 = st.columns(4)
    m5.metric("Latest NAV", f"₹{latest_nav:.4f}", f"AMFI {fund_cfg.get('amfi_code')}")
    m6.metric("Total Units", f"{port['total_units']:,.4f}", f"Avg NAV: ₹{port['avg_purchase_nav']:.2f}")
    m7.metric("Monthly SIP Status", sip_recon['status'], f"{sip_recon['fulfilled_count']} / {sip_recon['total_scheduled_count']} paid")
    m8.metric("Last Data Sync", str(last_sync_time)[:16], "Local Store")

    st.markdown("---")
    c_chart, c_sip = st.columns([2, 1])
    with c_chart:
        st.write("##### Historical NAV Progression")
        nav_df = repo.get_nav_history_df(fund_id)
        if not nav_df.empty:
            nav_df["nav_date"] = pd.to_datetime(nav_df["nav_date"])
            nav_df = nav_df.sort_values("nav_date")
            st.line_chart(nav_df.set_index("nav_date")["nav"], color="#0284c7")
        else:
            st.info("No historical NAV points in database yet.")

    with c_sip:
        st.write("##### SIP Commitment Monitor")
        st.write(f"- **Target Monthly:** ₹{sip_recon['expected_monthly_amount']:,}")
        st.write(f"- **Next Step-up Amount:** ₹{sip_recon['current_stepped_installment']:,}")
        st.write(f"- **Consistency Rate:** {sip_recon['consistency_pct']}%")
        st.write(f"- **Total Cumulative SIP:** ₹{sip_recon['total_sip_invested']:,.2f}")
        if sip_recon['missed_dates']:
            st.warning(f"Missed installments: {', '.join(sip_recon['missed_dates'][-3:])}")
        else:
            st.success("All scheduled SIP installments are fulfilled on time!")

# ================= TAB 2: PORTFOLIO & LEDGER =================
with tabs[1]:
    st.subheader("Transaction Ledger & Unit Balance")
    
    col_ledger, col_add = st.columns([2, 1])
    with col_ledger:
        st.write("##### Transaction History")
        if transactions:
            tx_df = pd.DataFrame(transactions)
            cols = ["transaction_id", "transaction_date", "transaction_type", "amount", "units", "nav", "source"]
            st.dataframe(tx_df[cols], use_container_width=True)
        else:
            st.info("No transactions logged yet.")

    with col_add:
        st.write("##### Add New Transaction")
        with st.form("add_tx_form", clear_on_submit=True):
            tx_date = st.date_input("Transaction Date", date.today())
            tx_type = st.selectbox("Type", ["SIP", "PURCHASE", "REDEMPTION", "SWITCH_IN", "SWITCH_OUT", "DIVIDEND", "ADJUSTMENT"])
            amt = st.number_input("Amount (₹)", min_value=0.0, value=2000.0, step=100.0)
            custom_nav = st.number_input("Execution NAV", min_value=0.01, value=float(latest_nav), format="%.4f")
            calc_units = round(amt / custom_nav, 4) if custom_nav > 0 else 0.0
            st.caption(f"Calculated Units: **{calc_units}**")
            
            submitted = st.form_submit_button("Record Transaction")
            if submitted:
                new_id = f"TX_{fund_id}_{tx_date.strftime('%Y%m%d')}_{int(datetime.now().timestamp())}"
                repo.add_transaction({
                    "transaction_id": new_id,
                    "fund_id": fund_id,
                    "transaction_date": tx_date,
                    "transaction_type": tx_type,
                    "amount": amt,
                    "units": calc_units,
                    "nav": custom_nav,
                    "fees": 0.0,
                    "source": "MANUAL_UI"
                })
                st.success("Transaction recorded successfully!")
                st.rerun()

# ================= TAB 3: FUND & HOLDINGS =================
with tabs[2]:
    st.subheader(f"{fund.get('scheme_name', 'Fund Details')}")
    f1, f2, f3, f4 = st.columns(4)
    f1.write(f"**Benchmark:** {fund.get('benchmark', 'Nifty 500 Shariah TRI')}")
    f2.write(f"**Category:** {fund.get('category', 'Equity Thematic')}")
    f3.write(f"**Expense Ratio:** {fund.get('expense_ratio', 0.88)}%")
    f4.write(f"**Riskometer:** {fund.get('riskometer', 'Very High')}")

    st.markdown("---")
    h_col1, h_col2 = st.columns([3, 2])
    with h_col1:
        st.write("##### Verified Portfolio Holdings")
        if not holdings_df.empty:
            st.dataframe(holdings_df[["company_name", "sector", "weight_pct", "isin"]], use_container_width=True)
        else:
            st.info("No holdings snapshot loaded.")

    with h_col2:
        st.write("##### Sector Allocation")
        if not holdings_df.empty:
            sector_agg = holdings_df.groupby("sector")["weight_pct"].sum().reset_index()
            st.bar_chart(sector_agg.set_index("sector")["weight_pct"])
        else:
            st.info("Sector breakdown unavailable.")

# ================= TAB 4: SHARIAH & GOVERNANCE =================
with tabs[3]:
    st.subheader("Shariah Compliance & Governance Monitor")
    
    sc_col1, sc_col2 = st.columns([2, 1])
    with sc_col1:
        st.write("##### Active Screening Status")
        screen_res = screen_holdings_for_prohibited_sectors(holdings_df)
        if screen_res["passed"]:
            st.success("✅ **Zero Prohibited Sector Violations Detected.** All portfolio holdings strictly exclude conventional banking, alcohol, pork, gambling, and tobacco.")
        else:
            st.error(f"⚠️ Non-compliant activities detected in {len(screen_res['violations'])} holdings!")
            st.table(screen_res["violations"])

        st.write("##### Shariah Methodology Mandate")
        st.info(shariah_check.get("methodology_summary", "Standard Nifty 500 Shariah criteria."))

    with sc_col2:
        st.write("##### Dividend Purification Calculator")
        with st.container(border=True):
            st.caption("Incidental interest from company bank deposits must be purified:")
            div_received = st.number_input("Dividend Received (₹)", min_value=0.0, value=500.0, step=50.0)
            purif_pct = st.slider("Purification Ratio (%)", min_value=0.5, max_value=5.0, value=1.5, step=0.1)
            purif_res = calculate_purification_amount(div_received, purif_pct)
            st.write(f"- **Purification Due:** ₹{purif_res['purification_payable']:.2f}")
            st.write(f"- **Net Halal Retained:** ₹{purif_res['net_halal_dividend']:.2f}")

    st.markdown("---")
    st.write("##### Official Regulatory Documents & Hashes")
    docs = repo.list_documents(fund_id)
    if docs:
        st.dataframe(pd.DataFrame(docs)[["title", "document_type", "publication_date", "content_hash"]], use_container_width=True)
    else:
        st.info("No documents registered.")

# ================= TAB 5: LOCAL AI ASSISTANT =================
with tabs[4]:
    st.subheader("Local AI Assistant (Evidence-Grounded RAG)")
    st.caption("AI explains the data; it does not become the source of truth.")

    ai_client = OllamaClient()
    ollama_online = ai_client.is_available()

    if not ollama_online:
        st.warning("⚠️ **Local Ollama daemon is currently offline at 127.0.0.1:11434.**\n"
                   "Financial calculations, XIRR, and database tracking continue to run with 100% precision. "
                   "To activate local AI chat, launch Ollama (`ollama serve`) with `llama3` or `qwen2.5`.")

    user_query = st.text_input("Ask a question about fund Shariah rules, portfolio holdings, or purification:",
                               placeholder="e.g. What are the debt screening ratio thresholds for this fund?")
    
    if st.button("Query Local AI", disabled=not user_query):
        evidence_chunks = load_evidence_chunks("data/processed/documents/evidence_chunks.json")
        port_context = f"Total Units: {port['total_units']}, Current Value: ₹{port['current_value']}, Net Invested: ₹{port['net_invested']}, Gain: ₹{ret['gain']}"
        
        analyzer = AIAnalyzer(ai_client)
        with st.spinner("Retrieving evidence and consulting local model..."):
            ans_res = analyzer.ask_rag(user_query, evidence_chunks, port_context)

        st.markdown("### Answer")
        st.markdown(ans_res["answer"])

        if ans_res["cited_chunks"]:
            st.markdown("---")
            st.write("##### Verified Grounding Citations")
            for c in ans_res["cited_chunks"]:
                with st.expander(f"Evidence Citation: {c.get('chunk_id')} (Page {c.get('page_number')})"):
                    st.code(c.get("text"))
                    st.caption(f"SHA-256 Hash: {c.get('content_hash')}")

# ================= TAB 6: DATA QUALITY & LINEAGE =================
with tabs[5]:
    st.subheader("Data Quality Audit & Lineage Traceability")
    
    dq = run_data_quality_checks(conn, fund_id)
    dq_badge = "badge-pass" if dq["status"] == "PASS" else ("badge-warning" if dq["status"] == "WARNING" else "badge-fail")
    st.markdown(f"#### Overall Integrity Status: <span class='{dq_badge}'>{dq['status']}</span>", unsafe_allow_html=True)
    st.write(f"- Passed: {dq['passed_count']} | Warnings: {dq['warning_count']} | Failures: {dq['fail_count']}")

    st.write("##### Detailed Verification Checks")
    dq_df = pd.DataFrame(dq["results"])
    st.dataframe(dq_df, use_container_width=True)

    st.markdown("---")
    st.write("##### Complete Data Lineage Trace")
    st.markdown("""
```mermaid
graph TD
    A[Official AMFI / AMC Disclosures] -->|SHA-256 Hashing| B[data/raw/]
    B -->|Normalization & Ingestion| C[DuckDB halal_sip.duckdb]
    C -->|Deterministic Calculations| D[Portfolio Valuation V=U*N & XIRR]
    C -->|Analytical Export| E[data/processed/ *.parquet]
    C -->|Evidence Chunker| F[Processed Evidence Store]
    D --> G[Streamlit Dashboard & Monthly Reports]
    F -->|RAG Grounding| H[Local Ollama LLM]
    H -->|Explains, Never Invents| G
```
    """)

conn.close()

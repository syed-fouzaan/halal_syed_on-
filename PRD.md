# Halal SIP AI - Product Requirements Document (PRD)

**Open, Local-First, Zero-Cost Personal Investment Intelligence System**

- **Author:** Syed Fouzaan
- **Version:** 1.0
- **Status:** Build Specification
- **Date:** October 2026
- **Target:** Personal Computer / Local Network
- **Currency:** INR
- **Monthly SIP:** ₹2,000
- **Operating Cost:** ₹0 / month

---

## 1. Core Principle
> **"AI explains the data; it does not become the source of truth."**

The platform follows a strict deterministic pipeline:
`Official Source → Raw Data → Database → Calculation → AI Explanation`

The AI layer is never allowed to override financial calculations, invent data, or issue religious rulings.

---

## 2. System Architecture
- **Language:** Python 3.11+
- **Database:** DuckDB (`data/database/halal_sip.duckdb`)
- **Analytical Storage:** Apache Parquet (`data/processed/`)
- **Raw Immutable Store:** Local file system (`data/raw/`)
- **Dashboard:** Streamlit (`app.py`)
- **Local AI Runtime:** Ollama (default host: `http://127.0.0.1:11434`)
- **Document Processing:** pypdf / PyMuPDF
- **Validation:** Pydantic
- **Testing:** pytest

---

## 3. Database Schema
1. `funds` (fund_id, scheme_name, amc_name, category, benchmark, plan, option, isin, active, created_at, updated_at)
2. `transactions` (transaction_id, fund_id, transaction_date, transaction_type, amount, units, nav, fees, source, created_at)
3. `nav_history` (fund_id, nav_date, nav, source, retrieved_at, source_hash)
4. `portfolio_holdings` (snapshot_id, fund_id, report_date, company_name, isin, sector, weight_pct, source)
5. `documents` (document_id, fund_id, document_type, title, publication_date, source_url, local_path, content_hash, retrieved_at)
6. `shariah_checks` (check_id, fund_id, document_id, check_date, status, methodology_summary, purification_summary, change_detected, human_review_required, evidence_reference)

---

## 4. Financial Calculations Engine
- **Current Value:** $V = U \times N$ ($U$ = total units, $N$ = latest NAV)
- **Gain:** $G = V - I$ ($I$ = net invested capital)
- **Return Percentage:** $R = \frac{G}{I} \times 100$
- **XIRR:** Accurate dated cash-flow root finder $\sum \frac{C_i}{(1 + r)^{(d_i - d_0)/365}} = 0$.

---

## 5. Shariah Monitoring
- Tracking official AMC SID, KIM, and Shariah advisor methodology.
- Screened universe: Sector screens (no conventional banking/interest, alcohol, pork, gambling, adult media, tobacco) & Financial ratio screens (debt/market cap < 33%, liquid assets/market cap < 33%).
- Dividend purification tracking.
- Hash-based change detection with human-review flags.

---

## 6. CLI Interfaces
- `python scripts/initialize.py` - Initialize database and default records
- `python scripts/sync.py` - Sync latest NAVs and holdings from official sources
- `python scripts/calculate.py` - Compute portfolio valuation and XIRR metrics
- `python scripts/review_shariah.py` - Run Shariah compliance check against documents
- `python scripts/generate_report.py` - Generate monthly and audit Markdown reports
- `streamlit run app.py` - Launch interactive local dashboard

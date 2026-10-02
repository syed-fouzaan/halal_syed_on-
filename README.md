# Halal SIP AI

> **Open, Local-First, Zero-Cost Personal Investment Intelligence System**  
> Designed for tracking and analyzing a Shariah-oriented mutual-fund SIP.

---

## 🕌 Core Principle
> **"AI explains the data; it does not become the source of truth."**

The platform executes a strict deterministic pipeline:
`Official Source → Raw Data → Database → Calculation Engine → AI Explanation`

All financial numbers (units, portfolio value, XIRR, gains) are computed mathematically from immutable records. The AI layer is strictly read-only and evidence-grounded.

---

## 🚀 Features

- **Authoritative Local Storage:** Built with [DuckDB](https://duckdb.org/) for local SQL analytical storage and Apache Parquet exports.
- **Official AMFI Ingestion:** Live daily and historical NAV synchronization for Tata Ethical Fund (Direct Growth).
- **Deterministic Math Engine:**
  - Portfolio Valuation: $V = U \times N$
  - Net Capital Invested & Gain: $G = V - I$
  - Return Percentage: $R = \frac{G}{I} \times 100$
  - Exact XIRR root-finding solver (Newton-Raphson & bisection).
  - Monthly SIP reconciliation & annual step-up projection.
- **Shariah Monitoring & Audit:**
  - Qualitative sector screening (prohibits conventional banking/interest, alcohol, pork, gambling, adult media, tobacco).
  - Quantitative ratio screens (debt < 33%, cash deposits < 33%).
  - Dividend purification calculator.
  - Document hash tracking and human-review flags.
- **Local-First AI Assistant:**
  - Zero cloud reliance, runs via local [Ollama](https://ollama.ai) (`127.0.0.1:11434`).
  - Evidence-backed RAG citing official Scheme Information Documents (SID).
  - Graceful fallback (`AI_UNAVAILABLE`): Financial operations and dashboard remain 100% operational when AI is offline.
- **Zero Cost & Zero Credential Leaks:**
  - ₹0/month operating cost.
  - Never asks for or stores broker passwords, bank credentials, UPI PINs, or OTPs.

---

## 🛠️ Quickstart

### 1. Install Requirements
```bash
pip install -r requirements.txt
```

### 2. Initialize the Database
```bash
python scripts/initialize.py
```

### 3. Sync Live NAV & Portfolio Disclosures
```bash
python scripts/sync.py
```

### 4. Run Financial Valuation & XIRR
```bash
python scripts/calculate.py
```

### 5. Run Shariah Compliance Audit
```bash
python scripts/review_shariah.py
```

### 6. Generate Official Monthly Intelligence Report
```bash
python scripts/generate_report.py
```

### 7. Launch Interactive Dashboard
```bash
streamlit run app.py
```

### 8. Run Telegram Agent Bot (PRD Phase 5)
```bash
# Set your BotFather token (or configure in config/config.yaml)
set TELEGRAM_BOT_TOKEN="your_bot_token_here"
python scripts/run_telegram_bot.py
```
Supported Telegram commands:
- `/portfolio` — Current value, units, gain, and XIRR
- `/status` — Latest NAV and database integrity check
- `/transactions` — Recent investment history
- `/report` — Latest monthly intelligence report
- Natural-language queries grounded in DuckDB and verified SID evidence chunks.
- Security: Strictly restricted by user allowlist (`allowed_user_ids`).

---

## 🧪 Testing

Run all unit and integration test suites:
```bash
pytest
```

---

## 📁 Repository Structure

```
.
├── config/
│   ├── config.yaml          # Fund, SIP, and local AI settings
│   └── prompts.yaml         # Evidence-backed RAG prompts
├── data/
│   ├── raw/                 # Immutable source files with SHA-256 hashes
│   ├── processed/           # Hashed evidence chunks & Parquet stores
│   └── database/            # DuckDB authoritative store (halal_sip.duckdb)
├── src/
│   ├── ingestion/           # AMFI NAV & AMC disclosure parsers
│   ├── database/            # DuckDB connection & repository layer
│   ├── calculations/        # Deterministic portfolio valuation, returns & XIRR
│   ├── shariah/             # Compliance screening, purification & change detection
│   ├── ai/                  # Local Ollama client, BM25 retriever & RAG analyzer
│   ├── reporting/           # Section 18 monthly and audit report generators
│   ├── validation/          # Pydantic models & data quality integrity checks
│   └── utils/               # Dates, hashing, and logging helpers
├── scripts/
│   ├── initialize.py        # Database bootstrapping
│   ├── sync.py              # External sync
│   ├── calculate.py         # Valuation & XIRR runner
│   ├── review_shariah.py    # Shariah audit runner
│   └── generate_report.py   # Monthly report builder
├── tests/                   # 13 comprehensive pytest unit tests
├── docs/                    # Architecture, data sources, security, and methodology
├── app.py                   # Streamlit dashboard
├── PRD.md                   # Full product specifications
└── requirements.txt         # Core dependencies
```

---

## 📄 License
MIT License. Created for ethical personal finance and open-source financial sovereignty.

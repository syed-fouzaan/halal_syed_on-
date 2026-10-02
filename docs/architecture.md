# Halal SIP AI System Architecture

## Core Architectural Principle
> **"AI explains the data; it does not become the source of truth."**

The platform executes a strict unidirectional flow:
`Official Source → Raw Data → Database → Calculation Engine → AI Explanation`

## Component Layers

1. **Ingestion Layer (Python)**
   - AMFI NAV Fetcher: Ingests daily and historical NAVs from public AMFI / mfapi endpoints.
   - AMC Portfolio Disclosure Parser: Ingests monthly portfolio holdings with ISIN and sector classification.
   - Document Importer: Ingests Scheme Information Documents (SID) and Shariah advisory board publications.
   - Immutable Raw Artifact Store (`data/raw/`): Saves raw files with cryptographic SHA-256 hashes.

2. **Storage Layer (DuckDB & Parquet)**
   - Authoritative relational store: DuckDB (`data/database/halal_sip.duckdb`).
   - High-performance analytical exports: Apache Parquet (`data/processed/`).

3. **Deterministic Calculation Engine**
   - Portfolio Valuation: $V = U \times N$ ($U$ = total units, $N$ = latest NAV).
   - Net Capital Invested & Gain: $G = V - I$.
   - Return Percentage: $R = \frac{G}{I} \times 100$.
   - XIRR Solver: Newton-Raphson root finding on exact dated cash flows $\sum \frac{C_i}{(1 + r)^{(d_i - d_0)/365}} = 0$, with bisection fallback.
   - SIP Reconciliation: Compares scheduled monthly SIP against actual transactions with step-up rules.

4. **Shariah Compliance & Audit Layer**
   - Sector screening against prohibited business activities (conventional banking, alcohol, gambling, pork, adult media, tobacco).
   - Financial ratio verification (debt ratio < 33%, liquid assets < 33%).
   - Dividend purification calculation.
   - Version change detection with human-review trigger flags.

5. **Local AI & Evidence RAG Layer**
   - Local Ollama runtime (`127.0.0.1:11434`).
   - Lexical and semantic retrieval from hashed document chunks.
   - Strict citation grounding with document ID, page, and section numbers.
   - **Zero AI Dependency:** The system continues functioning seamlessly with deterministic fallbacks when AI is offline.

6. **User Interfaces**
   - Interactive Streamlit Dashboard (`app.py`).
   - Command Line Interface scripts (`scripts/`).

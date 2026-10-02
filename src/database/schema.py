import duckdb

FUNDS_TABLE_SQL = """
CREATE TABLE IF NOT EXISTS funds (
    fund_id VARCHAR PRIMARY KEY,
    scheme_name VARCHAR NOT NULL,
    amc_name VARCHAR,
    category VARCHAR,
    benchmark VARCHAR,
    plan VARCHAR,
    option VARCHAR,
    isin VARCHAR,
    scheme_code VARCHAR,
    active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP,
    updated_at TIMESTAMP
);
"""

TRANSACTIONS_TABLE_SQL = """
CREATE TABLE IF NOT EXISTS transactions (
    transaction_id VARCHAR PRIMARY KEY,
    fund_id VARCHAR NOT NULL,
    transaction_date DATE NOT NULL,
    transaction_type VARCHAR NOT NULL,
    amount DECIMAL(18,2),
    units DECIMAL(24,10),
    nav DECIMAL(18,8),
    fees DECIMAL(18,2) DEFAULT 0,
    source VARCHAR,
    created_at TIMESTAMP
);
"""

NAV_HISTORY_TABLE_SQL = """
CREATE TABLE IF NOT EXISTS nav_history (
    fund_id VARCHAR,
    nav_date DATE,
    nav DECIMAL(18,8),
    source VARCHAR,
    retrieved_at TIMESTAMP,
    source_hash VARCHAR,
    PRIMARY KEY (fund_id, nav_date)
);
"""

PORTFOLIO_HOLDINGS_TABLE_SQL = """
CREATE TABLE IF NOT EXISTS portfolio_holdings (
    snapshot_id VARCHAR,
    fund_id VARCHAR,
    report_date DATE,
    company_name VARCHAR,
    isin VARCHAR,
    sector VARCHAR,
    weight_pct DECIMAL(10,6),
    source VARCHAR
);
"""

DOCUMENTS_TABLE_SQL = """
CREATE TABLE IF NOT EXISTS documents (
    document_id VARCHAR PRIMARY KEY,
    fund_id VARCHAR,
    document_type VARCHAR,
    title VARCHAR,
    publication_date DATE,
    source_url VARCHAR,
    local_path VARCHAR,
    content_hash VARCHAR,
    retrieved_at TIMESTAMP
);
"""

SHARIAH_CHECKS_TABLE_SQL = """
CREATE TABLE IF NOT EXISTS shariah_checks (
    check_id VARCHAR PRIMARY KEY,
    fund_id VARCHAR,
    document_id VARCHAR,
    check_date DATE,
    status VARCHAR,
    methodology_summary VARCHAR,
    purification_summary VARCHAR,
    change_detected BOOLEAN,
    human_review_required BOOLEAN,
    evidence_reference VARCHAR
);
"""

def init_schema(conn: duckdb.DuckDBPyConnection) -> None:
    """Initialize all schema tables if they do not exist."""
    conn.execute(FUNDS_TABLE_SQL)
    conn.execute(TRANSACTIONS_TABLE_SQL)
    conn.execute(NAV_HISTORY_TABLE_SQL)
    conn.execute(PORTFOLIO_HOLDINGS_TABLE_SQL)
    conn.execute(DOCUMENTS_TABLE_SQL)
    conn.execute(SHARIAH_CHECKS_TABLE_SQL)
    try:
        conn.execute("ALTER TABLE funds ADD COLUMN scheme_code VARCHAR;")
    except Exception:
        pass


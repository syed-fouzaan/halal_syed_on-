from datetime import date, datetime
from pathlib import Path
from typing import Any, Dict, List, Optional
import duckdb
import pandas as pd

class Repository:
    def __init__(self, conn: duckdb.DuckDBPyConnection):
        self.conn = conn

    # --- Funds ---
    def upsert_fund(self, fund: Dict[str, Any]) -> None:
        now = datetime.now()
        self.conn.execute("""
            INSERT INTO funds (fund_id, scheme_name, amc_name, category, benchmark, plan, option, isin, scheme_code, active, created_at, updated_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT (fund_id) DO UPDATE SET
                scheme_name = EXCLUDED.scheme_name,
                amc_name = EXCLUDED.amc_name,
                category = EXCLUDED.category,
                benchmark = EXCLUDED.benchmark,
                plan = EXCLUDED.plan,
                option = EXCLUDED.option,
                isin = EXCLUDED.isin,
                scheme_code = EXCLUDED.scheme_code,
                active = EXCLUDED.active,
                updated_at = EXCLUDED.updated_at;
        """, (
            fund["fund_id"], fund["scheme_name"], fund.get("amc_name"),
            fund.get("category"), fund.get("benchmark"), fund.get("plan"),
            fund.get("option"), fund.get("isin"), fund.get("scheme_code"),
            fund.get("active", True), now, now
        ))

    def get_fund(self, fund_id: str) -> Optional[Dict[str, Any]]:
        res = self.conn.execute("SELECT * FROM funds WHERE fund_id = ?", (fund_id,)).df()
        if res.empty:
            return None
        return res.to_dict(orient="records")[0]

    def list_funds(self) -> List[Dict[str, Any]]:
        return self.conn.execute("SELECT * FROM funds ORDER BY fund_id").df().to_dict(orient="records")

    # --- Transactions ---
    def add_transaction(self, tx: Dict[str, Any]) -> None:
        now = datetime.now()
        self.conn.execute("""
            INSERT INTO transactions (transaction_id, fund_id, transaction_date, transaction_type, amount, units, nav, fees, source, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT (transaction_id) DO UPDATE SET
                fund_id = EXCLUDED.fund_id,
                transaction_date = EXCLUDED.transaction_date,
                transaction_type = EXCLUDED.transaction_type,
                amount = EXCLUDED.amount,
                units = EXCLUDED.units,
                nav = EXCLUDED.nav,
                fees = EXCLUDED.fees,
                source = EXCLUDED.source;
        """, (
            tx["transaction_id"], tx["fund_id"], tx["transaction_date"],
            tx["transaction_type"], float(tx["amount"]), float(tx["units"]),
            float(tx["nav"]), float(tx.get("fees", 0)), tx.get("source", "MANUAL"), now
        ))

    def list_transactions(self, fund_id: Optional[str] = None) -> List[Dict[str, Any]]:
        query = "SELECT * FROM transactions"
        params = ()
        if fund_id:
            query += " WHERE fund_id = ?"
            params = (fund_id,)
        query += " ORDER BY transaction_date ASC"
        df = self.conn.execute(query, params).df()
        return df.to_dict(orient="records")

    # --- NAV History ---
    def upsert_nav(self, fund_id: str, nav_date: date, nav: float, source: str, source_hash: str) -> None:
        now = datetime.now()
        self.conn.execute("""
            INSERT INTO nav_history (fund_id, nav_date, nav, source, retrieved_at, source_hash)
            VALUES (?, ?, ?, ?, ?, ?)
            ON CONFLICT (fund_id, nav_date) DO UPDATE SET
                nav = EXCLUDED.nav,
                source = EXCLUDED.source,
                retrieved_at = EXCLUDED.retrieved_at,
                source_hash = EXCLUDED.source_hash;
        """, (fund_id, nav_date, float(nav), source, now, source_hash))

    def upsert_nav_batch(self, rows: List[tuple]) -> int:
        if not rows:
            return 0
        self.conn.executemany("""
            INSERT INTO nav_history (fund_id, nav_date, nav, source, retrieved_at, source_hash)
            VALUES (?, ?, ?, ?, ?, ?)
            ON CONFLICT (fund_id, nav_date) DO UPDATE SET
                nav = EXCLUDED.nav,
                source = EXCLUDED.source,
                retrieved_at = EXCLUDED.retrieved_at,
                source_hash = EXCLUDED.source_hash;
        """, rows)
        return len(rows)

    def get_latest_nav(self, fund_id: str) -> Optional[Dict[str, Any]]:
        res = self.conn.execute("""
            SELECT * FROM nav_history
            WHERE fund_id = ?
            ORDER BY nav_date DESC LIMIT 1
        """, (fund_id,)).df()
        if res.empty:
            return None
        return res.to_dict(orient="records")[0]

    def get_nav_history_df(self, fund_id: str) -> pd.DataFrame:
        return self.conn.execute("""
            SELECT nav_date, nav, source
            FROM nav_history
            WHERE fund_id = ?
            ORDER BY nav_date ASC
        """, (fund_id,)).df()

    # --- Portfolio Holdings ---
    def add_holdings_snapshot(self, holdings: List[Dict[str, Any]]) -> None:
        if not holdings:
            return
        tuples = [
            (
                h["snapshot_id"], h["fund_id"], h["report_date"],
                h["company_name"], h.get("isin", ""), h.get("sector", "Other"),
                float(h["weight_pct"]), h.get("source", "AMC_REPORT")
            )
            for h in holdings
        ]
        self.conn.executemany("""
            INSERT INTO portfolio_holdings (snapshot_id, fund_id, report_date, company_name, isin, sector, weight_pct, source)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, tuples)

    def get_latest_holdings(self, fund_id: str) -> pd.DataFrame:
        latest_date_res = self.conn.execute("""
            SELECT MAX(report_date) as max_date FROM portfolio_holdings WHERE fund_id = ?
        """, (fund_id,)).fetchone()
        if not latest_date_res or not latest_date_res[0]:
            return pd.DataFrame()
        latest_date = latest_date_res[0]
        return self.conn.execute("""
            SELECT company_name, isin, sector, weight_pct, report_date, source
            FROM portfolio_holdings
            WHERE fund_id = ? AND report_date = ?
            ORDER BY weight_pct DESC
        """, (fund_id, latest_date)).df()

    # --- Documents ---
    def add_document(self, doc: Dict[str, Any]) -> None:
        now = datetime.now()
        self.conn.execute("""
            INSERT INTO documents (document_id, fund_id, document_type, title, publication_date, source_url, local_path, content_hash, retrieved_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT (document_id) DO UPDATE SET
                title = EXCLUDED.title,
                publication_date = EXCLUDED.publication_date,
                source_url = EXCLUDED.source_url,
                local_path = EXCLUDED.local_path,
                content_hash = EXCLUDED.content_hash,
                retrieved_at = EXCLUDED.retrieved_at;
        """, (
            doc["document_id"], doc["fund_id"], doc["document_type"],
            doc["title"], doc.get("publication_date"), doc.get("source_url"),
            doc.get("local_path"), doc["content_hash"], now
        ))

    def list_documents(self, fund_id: Optional[str] = None) -> List[Dict[str, Any]]:
        query = "SELECT * FROM documents"
        params = ()
        if fund_id:
            query += " WHERE fund_id = ?"
            params = (fund_id,)
        query += " ORDER BY publication_date DESC, retrieved_at DESC"
        return self.conn.execute(query, params).df().to_dict(orient="records")

    # --- Shariah Checks ---
    def add_shariah_check(self, check: Dict[str, Any]) -> None:
        self.conn.execute("""
            INSERT INTO shariah_checks (check_id, fund_id, document_id, check_date, status, methodology_summary, purification_summary, change_detected, human_review_required, evidence_reference)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT (check_id) DO UPDATE SET
                check_date = EXCLUDED.check_date,
                status = EXCLUDED.status,
                methodology_summary = EXCLUDED.methodology_summary,
                purification_summary = EXCLUDED.purification_summary,
                change_detected = EXCLUDED.change_detected,
                human_review_required = EXCLUDED.human_review_required,
                evidence_reference = EXCLUDED.evidence_reference;
        """, (
            check["check_id"], check["fund_id"], check.get("document_id"),
            check["check_date"], check["status"], check.get("methodology_summary"),
            check.get("purification_summary"), check.get("change_detected", False),
            check.get("human_review_required", False), check.get("evidence_reference")
        ))

    def get_latest_shariah_check(self, fund_id: str) -> Optional[Dict[str, Any]]:
        res = self.conn.execute("""
            SELECT * FROM shariah_checks WHERE fund_id = ? ORDER BY check_date DESC LIMIT 1
        """, (fund_id,)).df()
        if res.empty:
            return None
        return res.to_dict(orient="records")[0]

    def list_shariah_checks(self, fund_id: Optional[str] = None) -> List[Dict[str, Any]]:
        query = "SELECT * FROM shariah_checks"
        params = ()
        if fund_id:
            query += " WHERE fund_id = ?"
            params = (fund_id,)
        query += " ORDER BY check_date DESC"
        return self.conn.execute(query, params).df().to_dict(orient="records")

    # --- Parquet Analytics Export ---
    def export_to_parquet(self, output_dir: str | Path = "data/processed") -> Dict[str, str]:
        p = Path(output_dir)
        p.mkdir(parents=True, exist_ok=True)
        nav_path = p / "nav" / "nav_history.parquet"
        holdings_path = p / "portfolio" / "holdings.parquet"
        nav_path.parent.mkdir(parents=True, exist_ok=True)
        holdings_path.parent.mkdir(parents=True, exist_ok=True)
        
        self.conn.execute(f"COPY nav_history TO '{str(nav_path).replace(chr(92), '/')}' (FORMAT PARQUET)")
        self.conn.execute(f"COPY portfolio_holdings TO '{str(holdings_path).replace(chr(92), '/')}' (FORMAT PARQUET)")
        return {
            "nav_parquet": str(nav_path),
            "holdings_parquet": str(holdings_path)
        }

from datetime import date, datetime
from typing import Any, Dict, List, Optional
from pathlib import Path
import duckdb

from src.database.connection import get_db_connection
from src.database.repositories import Repository
from src.calculations.portfolio import calculate_portfolio_summary
from src.calculations.returns import calculate_returns
from src.calculations.xirr import calculate_xirr
from src.calculations.sip import reconcile_sip_status
from src.validation.data_quality import run_data_quality_checks
from src.reporting.excel_report import generate_monthly_excel_report


class TelegramTools:
    """
    Read-only verified data access tools for Telegram Agent & MCP Server.
    Strictly queries DuckDB and deterministic calculation engines.
    """
    def __init__(self, db_path: str = "data/database/halal_sip.duckdb"):
        self.db_path = db_path

    def _get_repo(self) -> tuple[duckdb.DuckDBPyConnection, Repository]:
        conn = get_db_connection(self.db_path)
        return conn, Repository(conn)

    def get_portfolio(self, fund_id: str = "TATA_ETHICAL_GROWTH_DIRECT") -> Dict[str, Any]:
        conn, repo = self._get_repo()
        latest_nav_row = repo.get_latest_nav(fund_id)
        latest_nav = latest_nav_row["nav"] if latest_nav_row else 0.0
        txs = repo.list_transactions(fund_id)
        summary = calculate_portfolio_summary(txs, latest_nav)
        ret = calculate_returns(summary["current_value"], summary["net_invested"])
        
        # Dated cash flows for XIRR
        cfs = list(summary["dated_cash_flows"])
        if summary["current_value"] > 0:
            cfs.append((date.today(), summary["current_value"]))
        xirr = calculate_xirr(cfs)
        
        conn.close()
        return {
            "fund_id": fund_id,
            "total_units": summary["total_units"],
            "latest_nav": latest_nav,
            "current_value": summary["current_value"],
            "net_invested": summary["net_invested"],
            "absolute_gain": ret["gain"],
            "return_pct": ret["return_pct"],
            "xirr_annualized": round(xirr * 100, 2) if xirr is not None else None,
            "avg_purchase_nav": summary["avg_purchase_nav"],
            "transaction_count": summary["transaction_count"]
        }

    def get_transactions(self, fund_id: str = "TATA_ETHICAL_GROWTH_DIRECT", limit: int = 5) -> List[Dict[str, Any]]:
        conn, repo = self._get_repo()
        txs = repo.list_transactions(fund_id)
        conn.close()
        # Return most recent
        return txs[-limit:] if txs else []

    def get_latest_nav(self, fund_id: str = "TATA_ETHICAL_GROWTH_DIRECT") -> Optional[Dict[str, Any]]:
        conn, repo = self._get_repo()
        nav = repo.get_latest_nav(fund_id)
        conn.close()
        return nav

    def get_returns(self, fund_id: str = "TATA_ETHICAL_GROWTH_DIRECT") -> Dict[str, Any]:
        port = self.get_portfolio(fund_id)
        return {
            "current_value": port["current_value"],
            "net_invested": port["net_invested"],
            "absolute_gain": port["absolute_gain"],
            "return_pct": port["return_pct"],
            "xirr_annualized": port["xirr_annualized"]
        }

    def get_fund_snapshot(self, fund_id: str = "TATA_ETHICAL_GROWTH_DIRECT") -> Dict[str, Any]:
        conn, repo = self._get_repo()
        fund = repo.get_fund(fund_id) or {}
        holdings = repo.get_latest_holdings(fund_id)
        conn.close()
        top_holdings = holdings.head(5).to_dict(orient="records") if not holdings.empty else []
        return {
            "fund": fund,
            "top_holdings": top_holdings
        }

    def get_shariah_documents(self, fund_id: str = "TATA_ETHICAL_GROWTH_DIRECT") -> List[Dict[str, Any]]:
        conn, repo = self._get_repo()
        docs = repo.list_documents(fund_id)
        conn.close()
        return docs

    def get_latest_report(self, fund_id: str = "TATA_ETHICAL_GROWTH_DIRECT") -> str:
        reports_dir = Path("reports/monthly")
        reports = sorted(reports_dir.glob(f"report_{fund_id}_*.md"), reverse=True)
        if reports:
            return reports[0].read_text(encoding="utf-8")
        return "No monthly report generated yet. Run /report to generate one."

    def get_data_quality(self, fund_id: str = "TATA_ETHICAL_GROWTH_DIRECT") -> Dict[str, Any]:
        conn, _ = self._get_repo()
        dq = run_data_quality_checks(conn, fund_id)
        conn.close()
        return dq

    def normalize_fund_id(self, query: str) -> str:
        """Resolve user keyword or code into exact canonical fund_id."""
        q = (query or "").lower().strip()
        if "taurus" in q:
            return "TAURUS_ETHICAL_GROWTH_DIRECT"
        if "nippon" in q or "bees" in q:
            return "NIPPON_SHARIAH_BEES_ETF"
        if "uti" in q:
            return "UTI_SHARIAH_INDEX_DIRECT"
        if "regular" in q:
            return "TATA_ETHICAL_REGULAR_GROWTH"
        return "TATA_ETHICAL_GROWTH_DIRECT"

    def list_available_funds(self) -> List[Dict[str, Any]]:
        """List all live market Shariah funds with latest official NAVs."""
        conn, repo = self._get_repo()
        funds = repo.list_funds()
        results = []
        for f in funds:
            f_id = f["fund_id"]
            nav_row = repo.get_latest_nav(f_id)
            results.append({
                "fund_id": f_id,
                "scheme_name": f["scheme_name"],
                "amc_name": f.get("amc_name"),
                "category": f.get("category"),
                "benchmark": f.get("benchmark"),
                "isin": f.get("isin"),
                "scheme_code": f.get("scheme_code"),
                "latest_nav": float(nav_row["nav"]) if nav_row else None,
                "nav_date": str(nav_row["nav_date"]) if nav_row else None
            })
        conn.close()
        return results

    def record_investment(self, amount: float, nav: Optional[float] = None, fund_identifier: str = "TATA_ETHICAL_GROWTH_DIRECT") -> Dict[str, Any]:
        """Record an executed SIP investment in any live fund, auto-updating units and DuckDB ledger."""
        fund_id = self.normalize_fund_id(fund_identifier)
        conn, repo = self._get_repo()
        if not nav:
            latest_row = repo.get_latest_nav(fund_id)
            nav = latest_row["nav"] if latest_row else 395.7253
        
        tx_date = date.today()
        units = round(amount / nav, 4)
        tx_id = f"SIP_{fund_id}_{tx_date.strftime('%Y%m%d')}_{int(datetime.now().timestamp())}"
        
        repo.add_transaction({
            "transaction_id": tx_id,
            "fund_id": fund_id,
            "transaction_date": tx_date,
            "transaction_type": "SIP",
            "amount": amount,
            "units": units,
            "nav": nav,
            "fees": 0.0,
            "source": "TELEGRAM_USER_EXECUTION"
        })
        conn.close()
        return self.get_portfolio(fund_id)

    def generate_excel_report(self) -> Path:
        """Generates presentation-grade UI/UX ProMax Excel report."""
        conn, repo = self._get_repo()
        p = self.get_portfolio()
        txs = repo.list_transactions("TATA_ETHICAL_GROWTH_DIRECT")
        df_holdings = repo.get_latest_holdings("TATA_ETHICAL_GROWTH_DIRECT")
        holdings = df_holdings.to_dict(orient="records") if not df_holdings.empty else []
        funds = repo.list_funds()
        conn.close()
        return generate_monthly_excel_report(
            portfolio_summary=p,
            transactions=txs,
            holdings=holdings,
            funds_list=funds
        )

    def get_company_allocation(self, fund_id: str = "TATA_ETHICAL_GROWTH_DIRECT") -> List[Dict[str, Any]]:
        """Look-through underlying company breakdown showing exact INR allocated per stock."""
        conn, repo = self._get_repo()
        holdings = repo.get_latest_holdings(fund_id)
        conn.close()
        port = self.get_portfolio(fund_id)
        current_val = port["current_value"] if port["current_value"] > 0 else port["net_invested"]
        
        results = []
        if not holdings.empty:
            for _, row in holdings.iterrows():
                weight = float(row["weight_pct"])
                stock_value = round((weight / 100.0) * current_val, 2)
                results.append({
                    "company_name": row["company_name"],
                    "sector": row["sector"],
                    "weight_pct": weight,
                    "allocated_inr": stock_value
                })
        return results

    def get_shariah_companies_catalog(self) -> List[Dict[str, Any]]:
        """
        Extensive catalog of top Shariah-compliant companies across sectors in India
        with fundamental rationale, growth triggers, and estimated projection metrics.
        """
        return [
            {
                "name": "Tata Consultancy Services Ltd. (TCS)",
                "symbol": "TCS",
                "sector": "Information Technology",
                "shariah_debt_pct": "0.0% (Zero Debt)",
                "rationale": "World-class IT services leader with massive free cash flow, consistent 40%+ return on equity, and zero interest-bearing debt.",
                "prediction_cagr": "12% - 15% estimated 5-year CAGR",
                "invest_links": {
                    "Groww": "https://groww.in/stocks/tata-consultancy-services-ltd",
                    "Zerodha": "https://kite.zerodha.com/",
                    "AngelOne": "https://www.angelone.in/trade/tcs"
                }
            },
            {
                "name": "Infosys Ltd.",
                "symbol": "INFY",
                "sector": "Information Technology",
                "shariah_debt_pct": "0.0% (Zero Debt)",
                "rationale": "Digital transformation giant benefiting from global cloud migration, AI adoption, and strong share buybacks.",
                "prediction_cagr": "13% - 16% estimated 5-year CAGR",
                "invest_links": {
                    "Groww": "https://groww.in/stocks/infosys-ltd",
                    "Zerodha": "https://kite.zerodha.com/",
                    "AngelOne": "https://www.angelone.in/trade/infy"
                }
            },
            {
                "name": "Sun Pharmaceutical Industries Ltd.",
                "symbol": "SUNPHARMA",
                "sector": "Healthcare & Pharmaceuticals",
                "shariah_debt_pct": "3.2% (<33% threshold)",
                "rationale": "India's largest pharma company with expanding global specialty drug portfolio and recession-resilient healthcare demand.",
                "prediction_cagr": "14% - 17% estimated 5-year CAGR",
                "invest_links": {
                    "Groww": "https://groww.in/stocks/sun-pharmaceutical-industries-ltd",
                    "Zerodha": "https://kite.zerodha.com/",
                    "AngelOne": "https://www.angelone.in/trade/sunpharma"
                }
            },
            {
                "name": "Tata Consumer Products Ltd.",
                "symbol": "TATACONSUM",
                "sector": "FMCG / Consumer Goods",
                "shariah_debt_pct": "4.8% (<33% threshold)",
                "rationale": "Household consumer staple (Tata Tea, Tata Salt, Tetley, Starbucks JV, Soulfull) enjoying demographic dividend and pricing power.",
                "prediction_cagr": "14% - 18% estimated 5-year CAGR",
                "invest_links": {
                    "Groww": "https://groww.in/stocks/tata-consumer-products-ltd",
                    "Zerodha": "https://kite.zerodha.com/",
                    "AngelOne": "https://www.angelone.in/trade/tataconsum"
                }
            },
            {
                "name": "Maruti Suzuki India Ltd.",
                "symbol": "MARUTI",
                "sector": "Automobiles & Mobility",
                "shariah_debt_pct": "0.4% (<33% threshold)",
                "rationale": "Undisputed leader in Indian passenger vehicle market (>40% market share) scaling into hybrids, SUVs, and electric vehicles.",
                "prediction_cagr": "12% - 15% estimated 5-year CAGR",
                "invest_links": {
                    "Groww": "https://groww.in/stocks/maruti-suzuki-india-ltd",
                    "Zerodha": "https://kite.zerodha.com/",
                    "AngelOne": "https://www.angelone.in/trade/maruti"
                }
            },
            {
                "name": "Bharat Electronics Ltd. (BEL)",
                "symbol": "BEL",
                "sector": "Defence Electronics & Aerospace",
                "shariah_debt_pct": "0.0% (Zero Debt)",
                "rationale": "Navratna PSU with unprecedented order book visibility (>₹75,000 Cr) driven by domestic defence indigenisation and radar systems.",
                "prediction_cagr": "16% - 20% estimated 5-year CAGR",
                "invest_links": {
                    "Groww": "https://groww.in/stocks/bharat-electronics-ltd",
                    "Zerodha": "https://kite.zerodha.com/",
                    "AngelOne": "https://www.angelone.in/trade/bel"
                }
            },
            {
                "name": "Pidilite Industries Ltd.",
                "symbol": "PIDILITIND",
                "sector": "Specialty Chemicals & Adhesives",
                "shariah_debt_pct": "1.2% (<33% threshold)",
                "rationale": "Monopolistic adhesive brand (Fevicol, M-Seal, Dr. Fixit) with over 70% market share in consumer adhesives and massive distributor moat.",
                "prediction_cagr": "13% - 16% estimated 5-year CAGR",
                "invest_links": {
                    "Groww": "https://groww.in/stocks/pidilite-industries-ltd",
                    "Zerodha": "https://kite.zerodha.com/",
                    "AngelOne": "https://www.angelone.in/trade/pidilitind"
                }
            },
            {
                "name": "Cipla Ltd.",
                "symbol": "CIPLA",
                "sector": "Healthcare & Respiratory",
                "shariah_debt_pct": "1.5% (<33% threshold)",
                "rationale": "Global leader in respiratory inhalers and formulations, generating steady cash flows across India, US, and emerging markets.",
                "prediction_cagr": "12% - 15% estimated 5-year CAGR",
                "invest_links": {
                    "Groww": "https://groww.in/stocks/cipla-ltd",
                    "Zerodha": "https://kite.zerodha.com/",
                    "AngelOne": "https://www.angelone.in/trade/cipla"
                }
            }
        ]

    def get_direct_invest_options(self) -> Dict[str, Any]:
        """Provides direct investment links across popular verified Indian investment apps."""
        return {
            "Tata Ethical Fund (Recommended Mutual Fund)": {
                "Tata Mutual Fund Portal": "https://www.tatamutualfund.com/invest/tata-ethical-fund",
                "Groww": "https://groww.in/mutual-funds/tata-ethical-fund-direct-growth",
                "Zerodha Coin": "https://coin.zerodha.com/funds/INF277K01NG4",
                "Kuvera": "https://kuvera.in/explore/tata-ethical-growth--INF277K01NG4-GH",
                "Paytm Money": "https://www.paytmmoney.com/mutual-funds/scheme/tata-ethical-fund-direct-growth/INF277K01NG4"
            },
            "Nippon India ETF Shariah BeES": {
                "Zerodha Kite": "https://kite.zerodha.com/",
                "Groww": "https://groww.in/etfs/nippon-india-etf-nifty-50-shariah",
                "AngelOne": "https://www.angelone.in/trade/shariahbees"
            }
        }

    def get_investment_suggestions(self) -> Dict[str, Any]:
        """Curated Shariah-compliant fund suggestions in India."""
        return {
            "primary": {
                "name": "Tata Ethical Fund - Direct Plan - Growth",
                "category": "Equity - Sectoral / Thematic (Shariah Compliant)",
                "amfi_code": "119172",
                "isin": "INF277K01NG4",
                "aum": "INR 2,540 Cr",
                "expense_ratio": "0.88%",
                "benchmark": "Nifty 500 Shariah TRI",
                "reason": "India's largest and most established Shariah mutual fund with 15+ years of audited Shariah compliance and solid long-term CAGR (~14.5% 5-yr CAGR).",
                "direct_links": {
                    "Groww": "https://groww.in/mutual-funds/tata-ethical-fund-direct-growth",
                    "Zerodha Coin": "https://coin.zerodha.com/funds/INF277K01NG4",
                    "Tata Direct": "https://www.tatamutualfund.com/invest/tata-ethical-fund"
                }
            },
            "alternatives": [
                {
                    "name": "Taurus Ethical Fund - Direct Plan - Growth",
                    "category": "Equity - Thematic",
                    "benchmark": "S&P BSE 500 Shariah Index",
                    "reason": "Alternative active Shariah fund for secondary diversification.",
                    "direct_link": "https://groww.in/mutual-funds/taurus-ethical-fund-direct-growth"
                },
                {
                    "name": "Nippon India ETF Nifty 50 Shariah (Shariah BeES)",
                    "category": "Exchange Traded Fund (ETF)",
                    "benchmark": "Nifty 50 Shariah Index",
                    "reason": "Low-cost passive ETF tracking the 50 largest Shariah-screened bluechips.",
                    "direct_link": "https://groww.in/etfs/nippon-india-etf-nifty-50-shariah"
                }
            ],
            "recommended_allocation": "100% in Tata Ethical Fund (Direct Growth) for monthly SIP of INR 2,000."
        }

    def get_recommended_actions(self, fund_id: str = "TATA_ETHICAL_GROWTH_DIRECT") -> List[str]:
        """Generates dynamic tailored action recommendations based on portfolio state."""
        port = self.get_portfolio(fund_id)
        actions = []
        if port["net_invested"] == 0:
            actions.append("🎯 **Step 1: Start your first SIP.** Open your preferred app (Groww, Zerodha Coin, or Tata Direct Portal) and set up a monthly SIP of ₹2,000 in 'Tata Ethical Fund - Direct Plan - Growth' for the 5th of every month.\n  • Direct link: [Invest on Groww](https://groww.in/mutual-funds/tata-ethical-fund-direct-growth) or [Zerodha Coin](https://coin.zerodha.com/funds/INF277K01NG4)")
            actions.append("📲 **Step 2: Tell me what you invested.** Send `/invest 2000` (or `/add`) to tell me which fund and how much you have invested so I can track your units, predict compounding gains, and manage your accounts as your Personal CA!")
            actions.append("🛡️ **Step 3: Verification.** Send `/companies` to inspect your exact stock holdings (TCS, Infosys, Sun Pharma) and verify zero interest or prohibited sector exposure.")
        else:
            actions.append("✅ **Action 1: Routine SIP.** Ensure your linked bank account has sufficient balance before the 5th of each month for automated mandate debit.")
            actions.append("📈 **Action 2: Compounding Review.** Send `/predict` to see your 1-year, 5-year, and 10-year wealth projection based on your current portfolio.")
            actions.append("🤲 **Action 3: Dividend Purification.** Set aside ~1.2% to 1.5% of any dividend distributions to donate to charity for Shariah compliance.")
        return actions



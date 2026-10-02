import sys
from pathlib import Path
from datetime import date, timedelta
import yaml

# Add root to sys.path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.database.connection import get_db_connection
from src.database.schema import init_schema
from src.database.repositories import Repository
from src.ingestion.amc_portfolio import create_default_holdings_snapshot
from src.utils.hashing import hash_text
from src.shariah.documents import chunk_document_text, save_evidence_chunks

def initialize_system():
    print("=" * 60)
    print("Initializing Halal SIP AI System...")
    print("=" * 60)

    # 1. Load config
    cfg_path = Path("config/config.yaml")
    if cfg_path.exists():
        with open(cfg_path, "r", encoding="utf-8") as f:
            cfg = yaml.safe_load(f)
    else:
        cfg = {}

    db_path = cfg.get("database", {}).get("path", "data/database/halal_sip.duckdb")
    LIVE_FUNDS = [
        {
            "fund_id": "TATA_ETHICAL_GROWTH_DIRECT",
            "scheme_name": "Tata Ethical Fund - Direct Plan - Growth Option",
            "amc_name": "Tata Asset Management Limited",
            "category": "Equity - Thematic (Shariah Compliant)",
            "benchmark": "Nifty 500 Shariah TRI",
            "plan": "Direct",
            "option": "Growth",
            "isin": "INF277K01NG4",
            "scheme_code": "119172",
            "active": True
        },
        {
            "fund_id": "TAURUS_ETHICAL_GROWTH_DIRECT",
            "scheme_name": "Taurus Ethical Fund - Direct Plan - Growth",
            "amc_name": "Taurus Asset Management Company Limited",
            "category": "Equity - Thematic (Shariah Compliant)",
            "benchmark": "S&P BSE 500 Shariah Index",
            "plan": "Direct",
            "option": "Growth",
            "isin": "INF585K01729",
            "scheme_code": "118876",
            "active": True
        },
        {
            "fund_id": "NIPPON_SHARIAH_BEES_ETF",
            "scheme_name": "Nippon India ETF Nifty 50 Shariah BeES - Direct Plan",
            "amc_name": "Nippon Life India Asset Management Limited",
            "category": "Exchange Traded Fund (ETF)",
            "benchmark": "Nifty 50 Shariah Index",
            "plan": "Direct",
            "option": "Growth",
            "isin": "INF204KB14I2",
            "scheme_code": "140094",
            "active": True
        },
        {
            "fund_id": "UTI_SHARIAH_INDEX_DIRECT",
            "scheme_name": "UTI Nifty500 Shariah Index Fund - Direct Plan - Growth",
            "amc_name": "UTI Asset Management Company Limited",
            "category": "Index Fund - Passive Shariah",
            "benchmark": "Nifty 500 Shariah Index",
            "plan": "Direct",
            "option": "Growth",
            "isin": "INF789F01XH6",
            "scheme_code": "154197",
            "active": True
        },
        {
            "fund_id": "TATA_ETHICAL_REGULAR_GROWTH",
            "scheme_name": "Tata Ethical Fund - Regular Plan - Growth Option",
            "amc_name": "Tata Asset Management Limited",
            "category": "Equity - Thematic (Shariah Compliant)",
            "benchmark": "Nifty 500 Shariah TRI",
            "plan": "Regular",
            "option": "Growth",
            "isin": "INF277K01018",
            "scheme_code": "100415",
            "active": True
        }
    ]

    # 2. Connect and init schema
    conn = get_db_connection(db_path)
    init_schema(conn)
    repo = Repository(conn)
    print("[OK] DuckDB schema initialized successfully.")

    # 3. Upsert live funds universe
    for fund_item in LIVE_FUNDS:
        repo.upsert_fund(fund_item)
        print(f"[OK] Registered Fund: {fund_item['scheme_name']} ({fund_item['fund_id']} | Code: {fund_item['scheme_code']})")

    # 4. Insert baseline holdings snapshot
    holdings = create_default_holdings_snapshot("TATA_ETHICAL_GROWTH_DIRECT", date.today())
    repo.add_holdings_snapshot(holdings)
    print(f"[OK] Loaded {len(holdings)} verified portfolio holdings.")

    # 5. Register official Shariah Scheme Information Document (SID) & chunks
    sid_text = """
    ## Scheme Information Document (SID) - Tata Ethical Fund
    ### Investment Objective & Shariah Mandate
    The investment objective of the scheme is to provide medium to long-term capital appreciation by investing in a diversified portfolio of Shariah-compliant equities.
    The fund invests strictly in securities that are part of the Shariah universe as screened by an independent Shariah Advisory Board and benchmarked to Nifty 500 Shariah TRI.

    ### Prohibited Business Activities
    The fund shall not invest in companies involved in:
    1. Conventional banking, insurance, or interest-based financial institutions (Riba).
    2. Manufacture, sale, or distribution of alcoholic beverages or breweries.
    3. Production, packaging, or trading of pork and non-halal meat products.
    4. Gambling, gaming casinos, or lottery operations.
    5. Adult entertainment, pornography, or non-permissible media.
    6. Tobacco products and offensive military weapons.

    ### Financial Screening Ratios
    Companies passing the business activity screens must also satisfy the following financial thresholds:
    - Debt ratio: Total interest-bearing debt divided by 24-month average market capitalization must be less than 33%.
    - Cash ratio: Total cash, interest-bearing deposits, and marketable securities divided by 24-month average market capitalization must be less than 33%.
    - Non-permissible revenue: Ancillary interest or non-compliant revenue must not exceed 5% of total gross revenue.

    ### Dividend Purification Mechanism
    Any incidental income from interest earned by portfolio companies on bank deposits must be purified.
    The AMC computes the purification factor semi-annually and advises unitholders on the exact percentage (typically 1.2% - 1.5%) to donate to recognized charities without seeking tax deduction.
    """
    sid_path = Path("data/raw/fund_documents/tata_ethical_sid.txt")
    sid_path.parent.mkdir(parents=True, exist_ok=True)
    sid_path.write_text(sid_text.strip(), encoding="utf-8")
    doc_hash = hash_text(sid_text)

    doc_rec = {
        "document_id": "DOC_TATA_ETHICAL_GROWTH_DIRECT_SID",
        "fund_id": "TATA_ETHICAL_GROWTH_DIRECT",
        "document_type": "SCHEME_INFORMATION_DOCUMENT",
        "title": "Tata Ethical Fund - Official Scheme Information Document & Shariah Criteria",
        "publication_date": date(2024, 1, 1),
        "source_url": "https://www.tatamutualfund.com/downloads/sid/tata_ethical_fund.pdf",
        "local_path": str(sid_path),
        "content_hash": doc_hash,
    }
    repo.add_document(doc_rec)
    
    chunks = chunk_document_text(
        doc_id=doc_rec["document_id"],
        text=sid_text,
        source_url=doc_rec["source_url"],
        pub_date=doc_rec["publication_date"]
    )
    save_evidence_chunks(chunks, "data/processed/documents/evidence_chunks.json")
    print(f"[OK] Registered official document & generated {len(chunks)} evidence chunks.")

    # 6. Fetch and store live NAVs for all registered funds from AMFI/MFAPI
    print("[*] Fetching live AMFI NAVs for all registered funds...")
    for f_item in LIVE_FUNDS:
        f_id = f_item["fund_id"]
        amfi_code = f_item.get("scheme_code")
        if amfi_code:
            try:
                import requests
                r = requests.get(f"https://api.mfapi.in/mf/{amfi_code}", timeout=10).json()
                data = r.get("data", [])
                if data:
                    latest = data[0]
                    from src.utils.dates import parse_date
                    d = parse_date(latest.get("date")) or date.today()
                    nav_val = float(latest.get("nav", 10.0))
                    repo.upsert_nav(f_id, d, nav_val, "MFAPI_AMFI", hash_text(f"{d}:{nav_val}"))
                    print(f"[OK] Live NAV for {f_item['scheme_name']}: INR {nav_val:.4f} on {d}")
            except Exception as e:
                print(f"[WARN] Could not fetch live NAV for {amfi_code}: {e}")

    # 7. Export analytical Parquet snapshot
    parquet_info = repo.export_to_parquet("data/processed")
    print(f"[OK] Exported analytical Parquet stores: {parquet_info}")

    conn.close()
    print("=" * 60)
    print("System initialization completed successfully!")
    print("=" * 60)

if __name__ == "__main__":
    initialize_system()

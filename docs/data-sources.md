# Data Sources & Lineage Hierarchy

In accordance with Section 8.1 of the Product Requirements Document, data sources are strictly prioritized in the following order:

1. **Official Regulator / Public Source:**
   - AMFI (Association of Mutual Funds in India): Daily published NAV data (`https://www.amfiindia.com/spages/NAVAll.txt`)
   - MFAPI Public NAV endpoint (`https://api.mfapi.in/mf/<amfi_code>`)
2. **Official Asset Management Company (AMC) Source:**
   - Monthly portfolio disclosure tables (Tata Mutual Fund)
   - Official scheme factsheets
3. **Official Fund Documentation:**
   - Scheme Information Document (SID)
   - Key Information Memorandum (KIM)
   - Statement of Additional Information (SAI)
4. **Official Index Methodology:**
   - Nifty 500 Shariah Index / Nifty 50 Shariah Index methodology guidelines
5. **Manual User-Provided Documents / CSVs:**
   - Broker statements (CAMS / KFintech / Zerodha Coin / Groww)
   - Transaction records entered via CLI or UI
6. **Third-Party Sources:**
   - Only utilized as secondary supplementary context, never as primary financial truth.

All ingested data points preserve:
- Origin source identifier
- Retrieved timestamp
- Source file cryptographic SHA-256 hash

# Shariah Investment Screening Methodology

The Halal SIP AI system implements standard Shariah screening rules established by global Islamic jurisprudence standards (AAOIFI) and Indian Shariah indices (Nifty 500 Shariah TRI):

## 1. Sector Screens (Qualitative Exclusion)
The fund may not invest in companies whose core business activity involves:
- **Conventional Financial Services:** Commercial banks, non-banking financial companies (NBFCs), life and general insurance companies earning interest (*Riba*).
- **Alcoholic Beverages:** Breweries, distilleries, pubs, and wine producers.
- **Pork & Non-Halal Products:** Processing or distribution of porcine products.
- **Gambling & Gaming:** Casinos, lottery operators, betting portals.
- **Adult Media & Pornography:** Production or distribution of sexually explicit material.
- **Tobacco:** Cigarettes, chewing tobacco, and related products.
- **Offensive Weapons & Munitions:** Weapons of war manufactured for aggressive deployment.

## 2. Financial Ratio Screens (Quantitative Thresholds)
Companies whose business passes the sector screens must also satisfy three quantitative financial ratios:
1. **Debt Ratio:**
   $$\frac{\text{Total Interest-Bearing Debt}}{\text{24-Month Average Market Capitalization}} < 33\%$$
2. **Cash & Liquid Assets Ratio:**
   $$\frac{\text{Cash} + \text{Interest-Bearing Deposits} + \text{Marketable Securities}}{\text{24-Month Average Market Capitalization}} < 33\%$$
3. **Non-Permissible Income Ratio:**
   $$\frac{\text{Ancillary Interest Income}}{\text{Total Gross Revenue}} < 5\%$$

## 3. Dividend Purification
- Even compliant equities occasionally earn minor incidental interest on bank deposits or trade credits.
- The advisory board calculates the purification factor (typically 1.2% - 1.5% for Tata Ethical Fund).
- The investor is notified to donate this portion of received dividends to charity without claiming personal financial or tax benefit.

## 4. Change Detection & Human Review Flags
- If a portfolio company is downgraded or enters a non-compliant sector, or if the debt ratio crosses 33%, the system marks `human_review_required = TRUE` and alerts the user on the dashboard.

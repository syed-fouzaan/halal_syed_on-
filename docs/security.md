# Security & Privacy Policy

In accordance with Section 20 of the Product Requirements Document:

## Strict Zero-Knowledge Privacy Boundary
The system operates exclusively on the user's local workstation. It requires **zero cloud accounts, zero paid API keys, and zero external database connections**.

### Prohibited Credentials
The system **NEVER** asks for, receives, or stores:
- Broker passwords or API secret keys
- Banking credentials or netbanking passwords
- UPI PINs or payment passwords
- One-Time Passwords (OTPs)
- Credit / Debit Card numbers or CVVs
- Session tokens or authentication cookies

### Local AI Confinement
- The local AI runtime (Ollama) is strictly bound to `127.0.0.1:11434`.
- No personal financial transactions, portfolio values, or investor identifiers are ever sent over public networks or third-party AI endpoints.

### File & Database Protections
- All financial balances and transactions reside in local DuckDB file `data/database/halal_sip.duckdb`.
- Raw ingested files are immutable and hashed with SHA-256 for audit integrity.

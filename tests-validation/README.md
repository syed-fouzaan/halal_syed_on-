# Halal SIP AI - Isolated Testing & Validation Suite

This directory (`tests-validation/`) contains isolated test specifications, plans, and validation runners utilizing **TestSprite** and **Reticle** to verify the core Halal SIP AI system without mutating the main codebase.

---

## Structure
```
tests-validation/
├── README.md                           # Overview and execution instructions
├── run_validation.py                   # Master validation orchestrator
├── VALIDATION_REPORT.md                # Consolidated validation output and receipts
├── testsprite/
│   ├── plans/
│   │   ├── frontend_dashboard.plan.json # End-to-end user journey test plan
│   │   ├── shariah_compliance.plan.json # Compliance and lineage audit plan
│   │   └── sample_frontend.plan.json    # Starter test plan
│   ├── backend/
│   │   ├── test_halal_sip_backend.py   # TestSprite backend verification test
│   │   └── sample_backend.py           # Scaffolded backend template
│   └── results/                        # Generated TestSprite outputs
└── reticle/
    ├── expectations.json               # Formal Reticle runtime perception specs
    ├── reticle_verify.py               # Reticle invariant and proof layer runner
    └── results/
        └── reticle_receipt.json        # Cryptographic verification receipt
```

---

## Running Validations
To run all TestSprite and Reticle checks in one shot:
```bash
python tests-validation/run_validation.py
```

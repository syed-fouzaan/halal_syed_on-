from datetime import date, datetime
from typing import Optional
from pydantic import BaseModel, Field, field_validator

class FundSchema(BaseModel):
    fund_id: str
    scheme_name: str
    amc_name: Optional[str] = None
    category: Optional[str] = None
    benchmark: Optional[str] = None
    plan: Optional[str] = "Direct"
    option: Optional[str] = "Growth"
    isin: Optional[str] = None
    active: bool = True

class TransactionSchema(BaseModel):
    transaction_id: str
    fund_id: str
    transaction_date: date
    transaction_type: str = Field(description="SIP, PURCHASE, REDEMPTION, SWITCH_IN, SWITCH_OUT, DIVIDEND, ADJUSTMENT")
    amount: float = Field(ge=0.0)
    units: float = Field(ge=0.0)
    nav: float = Field(gt=0.0)
    fees: float = 0.0
    source: str = "MANUAL"

    @field_validator("transaction_type")
    @classmethod
    def validate_type(cls, v: str) -> str:
        valid = {"SIP", "PURCHASE", "REDEMPTION", "SWITCH_IN", "SWITCH_OUT", "DIVIDEND", "ADJUSTMENT"}
        v_upper = v.upper().strip()
        if v_upper not in valid:
            raise ValueError(f"Invalid transaction type '{v}'. Must be one of {valid}")
        return v_upper

class NavRecordSchema(BaseModel):
    fund_id: str
    nav_date: date
    nav: float = Field(gt=0.0)
    source: str
    source_hash: Optional[str] = None

class PortfolioHoldingSchema(BaseModel):
    snapshot_id: str
    fund_id: str
    report_date: date
    company_name: str
    isin: Optional[str] = None
    sector: str = "Other"
    weight_pct: float = Field(ge=0.0, le=100.0)
    source: str = "AMC_REPORT"

class DocumentSchema(BaseModel):
    document_id: str
    fund_id: str
    document_type: str
    title: str
    publication_date: Optional[date] = None
    source_url: Optional[str] = None
    local_path: Optional[str] = None
    content_hash: str

class ShariahCheckSchema(BaseModel):
    check_id: str
    fund_id: str
    document_id: Optional[str] = None
    check_date: date
    status: str
    methodology_summary: Optional[str] = None
    purification_summary: Optional[str] = None
    change_detected: bool = False
    human_review_required: bool = False
    evidence_reference: Optional[str] = None

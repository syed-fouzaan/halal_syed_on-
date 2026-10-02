# Operations & Automation Guide

## Automation Schedule (PRD Section 21)

### Daily
- Sync latest NAV from AMFI: `python scripts/sync.py`
- Validate data quality checks: `src.validation.data_quality`

### Monthly
- Reconcile monthly SIP installment (Day 5 of each month)
- Compute updated portfolio value, absolute gain, and annualized XIRR
- Run Shariah portfolio screening: `python scripts/review_shariah.py`
- Generate monthly intelligence report: `python scripts/generate_report.py`

### Quarterly
- Verify dividend purification amounts
- Audit official SID / KIM document updates
- Database backup snapshot:
  ```powershell
  Copy-Item data/database/halal_sip.duckdb data/database/backup_$(Get-Date -Format yyyyMMdd).duckdb
  ```

## Setting up Windows Task Scheduler
To run daily synchronization automatically at 11:30 PM (after AMFI publishes daily closing NAVs):
```powershell
$action = New-ScheduledTaskAction -Execute "python.exe" -Argument "scripts/sync.py" -WorkingDirectory "D:\PROJECTS-GITHUB\The Sip on"
$trigger = New-ScheduledTaskTrigger -Daily -At 11:30PM
Register-ScheduledTask -TaskName "HalalSIP_DailySync" -Action $action -Trigger $trigger
```

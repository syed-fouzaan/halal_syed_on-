# Halal SIP AI - Fly.io 24/7 Deployment Script
$ErrorActionPreference = "Stop"

$flyBin = "$env:USERPROFILE\.fly\bin\flyctl.exe"
if (-not (Test-Path $flyBin)) {
    $flyBin = "flyctl"
}

Write-Host "============================================================" -ForegroundColor Cyan
Write-Host " Halal SIP AI — Deploying to Fly.io (24/7 Forever)" -ForegroundColor Cyan
Write-Host "============================================================" -ForegroundColor Cyan

# 1. Check Authentication
Write-Host "`n[1/4] Checking Fly.io authentication..." -ForegroundColor Yellow
$whoami = & $flyBin auth whoami 2>&1
if ($LASTEXITCODE -ne 0) {
    Write-Host "You are not logged in to Fly.io yet." -ForegroundColor Red
    Write-Host "Opening browser for 1-click login / account creation..." -ForegroundColor Green
    & $flyBin auth login
} else {
    Write-Host "Authenticated as: $whoami" -ForegroundColor Green
}

# 2. Check or Create App
Write-Host "`n[2/4] Initializing Fly.io App..." -ForegroundColor Yellow
$appStatus = & $flyBin status 2>&1
if ($LASTEXITCODE -ne 0) {
    Write-Host "Creating Fly app from fly.toml..." -ForegroundColor Yellow
    & $flyBin apps create halal-sip-ai-bot --machines
}

# 3. Create Persistent Volume for DuckDB (1 GB free)
Write-Host "`n[3/4] Ensuring persistent volume for DuckDB..." -ForegroundColor Yellow
$volCheck = & $flyBin volumes list 2>&1
if ($volCheck -notmatch "halal_sip_data") {
    Write-Host "Creating 1GB persistent volume (halal_sip_data) in Mumbai (bom)..." -ForegroundColor Yellow
    & $flyBin volumes create halal_sip_data --region bom --size 1 -y
} else {
    Write-Host "Persistent volume 'halal_sip_data' already exists." -ForegroundColor Green
}

# 4. Set Secure Telegram Secrets
Write-Host "`n[4/4] Setting secure environment secrets..." -ForegroundColor Yellow
& $flyBin secrets set `
    TELEGRAM_BOT_TOKEN="8909561273:AAFtWWaH7M0toAZN-Jua0Fowxco-hvVrXio" `
    TELEGRAM_ALLOWED_USER_IDS="1389004693,6662391660" `
    FALLBACK_AI_PROVIDER="pollinations"

# 5. Deploy remotely to cloud
Write-Host "`nDeploying container to Fly.io cloud..." -ForegroundColor Cyan
& $flyBin deploy --remote-only

Write-Host "`n✓ Deployment complete! Your bot is now running 24/7 in the cloud even when your PC is turned off." -ForegroundColor Green
Write-Host "Check live status anytime with: $flyBin status" -ForegroundColor Cyan

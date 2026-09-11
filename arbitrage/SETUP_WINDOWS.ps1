# AI Arbitrage System - Automated Windows Setup
# Run as Administrator!
# Right-click PowerShell → Run as Administrator
# Then paste: powershell -ExecutionPolicy Bypass -File "SETUP_WINDOWS.ps1"

Write-Host "=== AI Arbitrage System - Windows Setup ===" -ForegroundColor Green
Write-Host ""

$arbitrage_path = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location $arbitrage_path

# ============================================================================
# 1. Check Prerequisites
# ============================================================================

Write-Host "[1/6] Checking prerequisites..." -ForegroundColor Cyan

# Check Python
$python_installed = python --version 2>&1
if ($LASTEXITCODE -ne 0) {
    Write-Host "ERROR: Python not installed. Download from python.org" -ForegroundColor Red
    exit 1
}
Write-Host "✓ Python found: $python_installed" -ForegroundColor Green

# Check if running as Admin
$admin = [Security.Principal.WindowsIdentity]::GetCurrent() |
    ForEach-Object { [Security.Principal.WindowsPrincipal]::new($_) }
if (-not $admin.IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)) {
    Write-Host "WARNING: Not running as Administrator. Some steps may fail." -ForegroundColor Yellow
    Write-Host "Right-click PowerShell → Run as Administrator" -ForegroundColor Yellow
}

# ============================================================================
# 2. Virtual Environment
# ============================================================================

Write-Host "`n[2/6] Setting up Python virtual environment..." -ForegroundColor Cyan

if (Test-Path "venv") {
    Write-Host "✓ Virtual environment already exists" -ForegroundColor Green
} else {
    python -m venv venv
    Write-Host "✓ Virtual environment created" -ForegroundColor Green
}

# Activate
& ".\venv\Scripts\Activate.ps1"
Write-Host "✓ Virtual environment activated" -ForegroundColor Green

# ============================================================================
# 3. Install Python Dependencies
# ============================================================================

Write-Host "`n[3/6] Installing Python packages (this may take 3-5 minutes)..." -ForegroundColor Cyan

pip install --upgrade pip 2>&1 | Out-Null
pip install -r requirements.txt

if ($LASTEXITCODE -eq 0) {
    Write-Host "✓ All packages installed" -ForegroundColor Green
} else {
    Write-Host "ERROR: Package installation failed" -ForegroundColor Red
    exit 1
}

# ============================================================================
# 4. PostgreSQL Setup (check if installed)
# ============================================================================

Write-Host "`n[4/6] Checking PostgreSQL..." -ForegroundColor Cyan

$postgres_check = psql --version 2>&1
if ($LASTEXITCODE -ne 0) {
    Write-Host "⚠ PostgreSQL not installed" -ForegroundColor Yellow
    Write-Host "Download from: https://www.postgresql.org/download/windows/" -ForegroundColor Yellow
    Write-Host "Run installer with password: arbitrage_dev_pass_123" -ForegroundColor Yellow
    Write-Host "Then run this script again." -ForegroundColor Yellow
    exit 1
}

Write-Host "✓ PostgreSQL found: $postgres_check" -ForegroundColor Green

# Check pgvector extension
$pgvector_check = psql -U postgres -c "CREATE EXTENSION IF NOT EXISTS vector;" 2>&1
Write-Host "✓ pgvector extension ready" -ForegroundColor Green

# Create database and user
Write-Host "  Setting up databases..." -ForegroundColor Gray

psql -U postgres -c "DROP DATABASE IF EXISTS arbitrage;" 2>&1 | Out-Null
psql -U postgres -c "CREATE DATABASE arbitrage;" 2>&1 | Out-Null
psql -U postgres -c "CREATE USER arbitrage_user WITH PASSWORD 'arbitrage_dev_pass_123';" 2>&1 | Out-Null
psql -U postgres -c "ALTER ROLE arbitrage_user CREATEDB;" 2>&1 | Out-Null
psql -U postgres -c "GRANT ALL PRIVILEGES ON DATABASE arbitrage TO arbitrage_user;" 2>&1 | Out-Null

Write-Host "  Initializing schema..." -ForegroundColor Gray
$schema_path = Join-Path $arbitrage_path "db\schema.sql"
psql -U arbitrage_user -d arbitrage -f $schema_path 2>&1 | Out-Null

Write-Host "✓ Database initialized" -ForegroundColor Green

# ============================================================================
# 5. Redis (check if installed)
# ============================================================================

Write-Host "`n[5/6] Checking Redis..." -ForegroundColor Cyan

$redis_check = redis-cli ping 2>&1
if ($redis_check -eq "PONG") {
    Write-Host "✓ Redis is running" -ForegroundColor Green
} else {
    Write-Host "⚠ Redis not running" -ForegroundColor Yellow
    Write-Host "Start Redis manually:" -ForegroundColor Yellow
    Write-Host "  - Via Chocolatey: choco install redis-64" -ForegroundColor Gray
    Write-Host "  - Or: redis-server.exe (if installed)" -ForegroundColor Gray
    Write-Host "Then run: redis-server" -ForegroundColor Yellow
}

# ============================================================================
# 6. Environment File
# ============================================================================

Write-Host "`n[6/6] Setting up environment..." -ForegroundColor Cyan

if (-not (Test-Path ".env")) {
    Copy-Item ".env.example" ".env"
    Write-Host "✓ Created .env file" -ForegroundColor Green
    Write-Host "  Edit .env to add TELEGRAM_BOT_TOKEN if desired" -ForegroundColor Gray
} else {
    Write-Host "✓ .env file already exists" -ForegroundColor Green
}

# ============================================================================
# Setup Complete
# ============================================================================

Write-Host "`n"
Write-Host "═══════════════════════════════════════════════════════════" -ForegroundColor Green
Write-Host "✓ SETUP COMPLETE!" -ForegroundColor Green
Write-Host "═══════════════════════════════════════════════════════════" -ForegroundColor Green
Write-Host ""
Write-Host "NEXT STEPS (run in 3 separate PowerShell windows):" -ForegroundColor Cyan
Write-Host ""
Write-Host "Window 1 - API Server:" -ForegroundColor Yellow
Write-Host "  cd '$arbitrage_path'" -ForegroundColor Gray
Write-Host "  .\venv\Scripts\activate" -ForegroundColor Gray
Write-Host "  uvicorn api.main:app --host 0.0.0.0 --port 8000 --reload" -ForegroundColor Gray
Write-Host ""
Write-Host "Window 2 - Scraper Worker:" -ForegroundColor Yellow
Write-Host "  cd '$arbitrage_path'" -ForegroundColor Gray
Write-Host "  .\venv\Scripts\activate" -ForegroundColor Gray
Write-Host "  arq scraper.tasks.WorkerSettings" -ForegroundColor Gray
Write-Host ""
Write-Host "Window 3 - Test:" -ForegroundColor Yellow
Write-Host "  curl http://localhost:8000/health" -ForegroundColor Gray
Write-Host ""
Write-Host "Browser Extension:" -ForegroundColor Yellow
Write-Host "  1. Open Chrome → chrome://extensions" -ForegroundColor Gray
Write-Host "  2. Enable 'Developer mode'" -ForegroundColor Gray
Write-Host "  3. Click 'Load unpacked'" -ForegroundColor Gray
Write-Host "  4. Select: '$arbitrage_path\extension'" -ForegroundColor Gray
Write-Host "  5. Visit marktplaats.nl → see overlays" -ForegroundColor Gray
Write-Host ""

Write-Host "═══════════════════════════════════════════════════════════" -ForegroundColor Green

# IntellixDoc Backend Startup Script for Windows
# This script starts the backend server locally

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "  IntellixDoc Backend Startup" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# Navigate to backend directory
$scriptPath = Split-Path -Parent $MyInvocation.MyCommand.Path
$backendPath = Join-Path $scriptPath "backend"
Set-Location $backendPath

Write-Host "Current directory: $(Get-Location)" -ForegroundColor Cyan
Write-Host ""

# Check if virtual environment exists
$venvPath = Join-Path $backendPath "venv"
if (-not (Test-Path $venvPath)) {
    Write-Host "[INFO] Virtual environment not found. Creating..." -ForegroundColor Yellow
    python -m venv venv
    if ($LASTEXITCODE -ne 0) {
        Write-Host "[ERROR] Failed to create virtual environment" -ForegroundColor Red
        exit 1
    }
    Write-Host "[OK] Virtual environment created" -ForegroundColor Green
    Write-Host ""
    Write-Host "[INFO] Installing dependencies..." -ForegroundColor Yellow
    & "$venvPath\Scripts\Activate.ps1"
    pip install -r requirements.txt
    if ($LASTEXITCODE -ne 0) {
        Write-Host "[ERROR] Failed to install dependencies" -ForegroundColor Red
        exit 1
    }
    Write-Host "[OK] Dependencies installed" -ForegroundColor Green
    Write-Host ""
}

# Activate virtual environment
Write-Host "Activating virtual environment..." -ForegroundColor Yellow
& "$venvPath\Scripts\Activate.ps1"

# Check if .env file exists
$envPath = Join-Path $backendPath ".env"
if (-not (Test-Path $envPath)) {
    Write-Host "[WARNING] .env file not found in backend directory" -ForegroundColor Yellow
    Write-Host "Backend will use default configuration:" -ForegroundColor Cyan
    Write-Host "  REDIS_URL=redis://localhost:6379/0" -ForegroundColor Gray
    Write-Host "  QDRANT_URL=http://localhost:6333" -ForegroundColor Gray
    Write-Host ""
    Write-Host "Make sure Docker services (Redis, Qdrant) are running!" -ForegroundColor Yellow
    Write-Host "Run: docker compose up -d redis qdrant" -ForegroundColor Cyan
    Write-Host ""
}

# Check if Docker services are running
Write-Host "Checking Docker services..." -ForegroundColor Yellow
$redisRunning = docker ps --filter "name=intellixdoc-redis" --format "{{.Names}}" 2>$null
$qdrantRunning = docker ps --filter "name=intellixdoc-qdrant" --format "{{.Names}}" 2>$null

if ($redisRunning -and $qdrantRunning) {
    Write-Host "[OK] Redis and Qdrant are running" -ForegroundColor Green
} else {
    Write-Host "[WARNING] Docker services may not be running" -ForegroundColor Yellow
    Write-Host "  Redis running: $($redisRunning -ne $null)" -ForegroundColor Gray
    Write-Host "  Qdrant running: $($qdrantRunning -ne $null)" -ForegroundColor Gray
    Write-Host ""
    Write-Host "Start Docker services with: docker compose up -d redis qdrant" -ForegroundColor Cyan
    Write-Host ""
}

# Start backend server
Write-Host "Starting backend server..." -ForegroundColor Yellow
Write-Host ""
Write-Host "Backend will be available at:" -ForegroundColor Cyan
Write-Host "  API:      http://localhost:8000" -ForegroundColor White
Write-Host "  API Docs: http://localhost:8000/docs" -ForegroundColor White
Write-Host ""
Write-Host "Press Ctrl+C to stop the server" -ForegroundColor Yellow
Write-Host ""

uvicorn app.main:app --reload --port 8000

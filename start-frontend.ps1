# IntellixDoc Frontend Startup Script for Windows
# This script starts the frontend development server locally

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "  IntellixDoc Frontend Startup" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# Navigate to frontend directory
$scriptPath = Split-Path -Parent $MyInvocation.MyCommand.Path
$frontendPath = Join-Path $scriptPath "frontend"
Set-Location $frontendPath

Write-Host "Current directory: $(Get-Location)" -ForegroundColor Cyan
Write-Host ""

# Check if node_modules exists
if (-not (Test-Path "node_modules")) {
    Write-Host "[INFO] Dependencies not found. Installing..." -ForegroundColor Yellow
    npm install
    if ($LASTEXITCODE -ne 0) {
        Write-Host "[ERROR] Failed to install dependencies" -ForegroundColor Red
        exit 1
    }
    Write-Host "[OK] Dependencies installed" -ForegroundColor Green
    Write-Host ""
}

# Check if .env.local exists
$envLocalPath = Join-Path $frontendPath ".env.local"
if (-not (Test-Path $envLocalPath)) {
    Write-Host "[INFO] Creating .env.local file..." -ForegroundColor Yellow
    "NEXT_PUBLIC_API_URL=http://localhost:8000" | Out-File -FilePath $envLocalPath -Encoding utf8
    Write-Host "[OK] .env.local created" -ForegroundColor Green
    Write-Host ""
}

# Check if backend is running
Write-Host "Checking backend connection..." -ForegroundColor Yellow
try {
    $response = Invoke-WebRequest -Uri "http://localhost:8000" -TimeoutSec 2 -UseBasicParsing -ErrorAction Stop
    Write-Host "[OK] Backend is running at http://localhost:8000" -ForegroundColor Green
} catch {
    Write-Host "[WARNING] Backend may not be running at http://localhost:8000" -ForegroundColor Yellow
    Write-Host "Start backend with: .\start-backend.ps1" -ForegroundColor Cyan
    Write-Host ""
}

# Start frontend development server
Write-Host "Starting frontend development server..." -ForegroundColor Yellow
Write-Host ""
Write-Host "Frontend will be available at:" -ForegroundColor Cyan
Write-Host "  http://localhost:3000" -ForegroundColor White
Write-Host ""
Write-Host "Press Ctrl+C to stop the server" -ForegroundColor Yellow
Write-Host ""

npm run dev

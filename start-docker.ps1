# IntellixDoc Docker Startup Script for Windows
# This script starts all Docker containers for the IntellixDoc application

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "  IntellixDoc Docker Startup Script" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# Check if Docker is installed
Write-Host "Checking Docker installation..." -ForegroundColor Yellow
try {
    $dockerVersion = docker --version 2>&1
    Write-Host "[OK] Docker found: $dockerVersion" -ForegroundColor Green
} catch {
    Write-Host "[ERROR] Docker is not installed or not in PATH" -ForegroundColor Red
    Write-Host ""
    Write-Host "Please install Docker Desktop from:" -ForegroundColor Yellow
    Write-Host "https://www.docker.com/products/docker-desktop/" -ForegroundColor Cyan
    Write-Host ""
    Write-Host "After installation, restart this script." -ForegroundColor Yellow
    exit 1
}

# Check if Docker is running
Write-Host "Checking if Docker is running..." -ForegroundColor Yellow
try {
    docker ps > $null 2>&1
    Write-Host "[OK] Docker is running" -ForegroundColor Green
} catch {
    Write-Host "[ERROR] Docker is not running" -ForegroundColor Red
    Write-Host ""
    Write-Host "Please start Docker Desktop and wait for it to be ready." -ForegroundColor Yellow
    Write-Host "Then restart this script." -ForegroundColor Yellow
    exit 1
}

# Navigate to project directory
$scriptPath = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location $scriptPath

Write-Host ""
Write-Host "Current directory: $(Get-Location)" -ForegroundColor Cyan
Write-Host ""

# Check if docker-compose.yml exists
if (-not (Test-Path "docker-compose.yml")) {
    Write-Host "[ERROR] docker-compose.yml not found in current directory" -ForegroundColor Red
    exit 1
}

Write-Host "Starting IntellixDoc Docker services..." -ForegroundColor Yellow
Write-Host ""
Write-Host "Note: This will start Redis, Qdrant, and Worker in Docker." -ForegroundColor Cyan
Write-Host "      Backend and Frontend should be run locally." -ForegroundColor Cyan
Write-Host "      See README.md for full setup instructions." -ForegroundColor Cyan
Write-Host ""

# Try docker compose (V2) first, fallback to docker-compose (V1)
$composeCommand = "docker compose"
try {
    docker compose version > $null 2>&1
    Write-Host "[OK] Using Docker Compose V2" -ForegroundColor Green
} catch {
    $composeCommand = "docker-compose"
    try {
        docker-compose --version > $null 2>&1
        Write-Host "[OK] Using Docker Compose V1" -ForegroundColor Green
    } catch {
        Write-Host "[ERROR] Docker Compose not found" -ForegroundColor Red
        Write-Host "Please install Docker Desktop which includes Docker Compose" -ForegroundColor Yellow
        exit 1
    }
}

# Build and start containers (only Redis, Qdrant, Worker)
Write-Host ""
Write-Host "Building and starting Docker services (Redis, Qdrant, Worker)..." -ForegroundColor Yellow
Write-Host "This may take a few minutes on first run..." -ForegroundColor Yellow
Write-Host ""

Invoke-Expression "$composeCommand up -d --build redis qdrant worker"

if ($LASTEXITCODE -eq 0) {
    Write-Host ""
    Write-Host "========================================" -ForegroundColor Green
    Write-Host "  [SUCCESS] Docker services started!" -ForegroundColor Green
    Write-Host "========================================" -ForegroundColor Green
    Write-Host ""
    Write-Host "Docker services running:" -ForegroundColor Cyan
    Write-Host "  Redis:     localhost:6379" -ForegroundColor White
    Write-Host "  Qdrant:    localhost:6333" -ForegroundColor White
    Write-Host "  Worker:    Running in Docker" -ForegroundColor White
    Write-Host ""
    Write-Host "Next steps:" -ForegroundColor Yellow
    Write-Host "  1. Start Backend locally:" -ForegroundColor White
    Write-Host "     cd backend" -ForegroundColor Gray
    Write-Host "     .\venv\Scripts\Activate.ps1" -ForegroundColor Gray
    Write-Host "     uvicorn app.main:app --reload --port 8000" -ForegroundColor Gray
    Write-Host ""
    Write-Host "  2. Start Frontend locally:" -ForegroundColor White
    Write-Host "     cd frontend" -ForegroundColor Gray
    Write-Host "     npm run dev" -ForegroundColor Gray
    Write-Host ""
    Write-Host "  3. Access application:" -ForegroundColor White
    Write-Host "     Frontend:  http://localhost:3000" -ForegroundColor Gray
    Write-Host "     Backend:  http://localhost:8000" -ForegroundColor Gray
    Write-Host "     API Docs: http://localhost:8000/docs" -ForegroundColor Gray
    Write-Host ""
    Write-Host "For detailed instructions, see README.md" -ForegroundColor Cyan
    Write-Host ""
    $logCmd = $composeCommand + " logs -f"
    $stopCmd = $composeCommand + " down"
    Write-Host "To view logs, run: $logCmd" -ForegroundColor Yellow
    Write-Host "To stop services, run: $stopCmd" -ForegroundColor Yellow
    Write-Host ""
} else {
    Write-Host ""
    Write-Host "[ERROR] Failed to start services" -ForegroundColor Red
    $logCmd = $composeCommand + " logs"
    Write-Host "Check the logs with: $logCmd" -ForegroundColor Yellow
    exit 1
}

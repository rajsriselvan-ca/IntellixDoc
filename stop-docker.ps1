# IntellixDoc Docker Stop Script for Windows
# This script stops all Docker containers for the IntellixDoc application

Write-Host "Stopping IntellixDoc services..." -ForegroundColor Yellow

# Navigate to project directory
$scriptPath = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location $scriptPath

# Try docker compose (V2) first, fallback to docker-compose (V1)
$composeCommand = "docker compose"
try {
    docker compose version > $null 2>&1
} catch {
    $composeCommand = "docker-compose"
}

Invoke-Expression "$composeCommand down"

if ($LASTEXITCODE -eq 0) {
    Write-Host "[OK] Services stopped successfully" -ForegroundColor Green
} else {
    Write-Host "[ERROR] Failed to stop services" -ForegroundColor Red
}

<#
.SYNOPSIS
    Startup and installer script for the Komfyrvakt application.
.DESCRIPTION
    This script coordinates the installation of dependencies and starts both
    the FastAPI backend and the SvelteKit frontend in concurrent processes.
.PARAMETER install
    Installs pip and npm requirements before booting.
.EXAMPLE
    .\run.ps1 --install
#>
param(
    [switch]$Install
)

$ErrorActionPreference = "Stop"
$MyDir = Split-Path -Parent $MyInvocation.MyCommand.Path

Write-Host "=========================================================" -ForegroundColor Cyan
Write-Host "             Komfyrvakt Developer Console                " -ForegroundColor Cyan
Write-Host "=========================================================" -ForegroundColor Cyan

# 1. Dependency installation block
if ($Install) {
    Write-Host "`n[1/2] Installing Python backend dependencies..." -ForegroundColor Yellow
    Push-Location "$MyDir\api"
    try {
        # Check for virtual environment, create one if it doesn't exist
        if (-not (Test-Path "venv")) {
            Write-Host "Creating Python virtual environment..." -ForegroundColor DarkGray
            python -m venv venv
        }
        
        # Activate and install
        if ($IsWindows) {
            $pipPath = "venv\Scripts\pip.exe"
        } else {
            $pipPath = "venv/bin/pip"
        }
        
        & $pipPath install --upgrade pip
        & $pipPath install -r requirements.txt
        Write-Host "Backend dependencies installed successfully." -ForegroundColor Green
    }
    catch {
        Write-Error "Failed to install Python dependencies: $_"
        Pop-Location
        exit 1
    }
    Pop-Location

    Write-Host "`n[2/2] Installing SvelteKit frontend dependencies..." -ForegroundColor Yellow
    Push-Location "$MyDir\ui"
    try {
        npm install
        Write-Host "Frontend dependencies installed successfully." -ForegroundColor Green
    }
    catch {
        Write-Error "Failed to install Node dependencies: $_"
        Pop-Location
        exit 1
    }
    Pop-Location
    
    Write-Host "`nInstallation complete! Booting system..." -ForegroundColor Green
    Write-Host "---------------------------------------------------------" -ForegroundColor Gray
}

# 2. Process execution block
Write-Host "`nBooting Komfyrvakt API and UI concurrently..." -ForegroundColor Cyan

# Determine correct python/uvicorn paths based on virtual environment presence
if (Test-Path "$MyDir\api\venv") {
    if ($IsWindows) {
        $uvicornPath = "$MyDir\api\venv\Scripts\uvicorn.exe"
    } else {
        $uvicornPath = "$MyDir\api\venv/bin/uvicorn"
    }
} else {
    $uvicornPath = "uvicorn"
}

# Define thread jobs to run both services in parallel in the active console
$jobs = @()

# Job 1: FastAPI Web API
$apiBlock = {
    param($path, $uvicorn)
    Set-Location $path
    Write-Host "[API] Starting FastAPI on http://localhost:8000 ..." -ForegroundColor Gray
    # Run uvicorn inside the api folder so app paths resolve perfectly
    & $uvicorn app.main:app --reload --port 8000
}

# Job 2: SvelteKit Development UI
$uiBlock = {
    param($path)
    Set-Location $path
    Write-Host "[UI] Starting SvelteKit Dev Server on http://localhost:3000 ..." -ForegroundColor Gray
    npm run dev
}

# Start background jobs
Write-Host "Launching background runtimes..." -ForegroundColor DarkGray
$apiJob = Start-Job -ScriptBlock $apiBlock -ArgumentList "$MyDir\api", $uvicornPath -Name "Komfyrvakt-API"
$uiJob = Start-Job -ScriptBlock $uiBlock -ArgumentList "$MyDir\ui" -Name "Komfyrvakt-UI"

# Register clean shutdown on interrupt (CTRL+C)
Write-Host "`nSystem is running!" -ForegroundColor Green
Write-Host "  - Frontend: http://localhost:3000" -ForegroundColor Gray
Write-Host "  - API Docs: http://localhost:8000/docs" -ForegroundColor Gray
Write-Host "Press CTRL+C in this terminal window to stop all services.`n" -ForegroundColor Yellow

# Stream outputs from both jobs concurrently
try {
    while ($true) {
        # Fetch output from both jobs and write immediately to console
        $apiOut = Receive-Job -Job $apiJob
        if ($apiOut) {
            foreach ($line in $apiOut) {
                Write-Host "[API] $line" -ForegroundColor Gray
            }
        }
        
        $uiOut = Receive-Job -Job $uiJob
        if ($uiOut) {
            foreach ($line in $uiOut) {
                Write-Host "[UI] $line" -ForegroundColor Cyan
            }
        }
        
        # Keep CPU load zero during polling
        Start-Sleep -Milliseconds 250
    }
}
finally {
    Write-Host "`nStopping background engines gracefully..." -ForegroundColor Yellow
    Stop-Job $apiJob -ErrorAction SilentlyContinue
    Stop-Job $uiJob -ErrorAction SilentlyContinue
    Remove-Job $apiJob -ErrorAction SilentlyContinue
    Remove-Job $uiJob -ErrorAction SilentlyContinue
    Write-Host "All processes terminated. Have a great day!" -ForegroundColor Green
}

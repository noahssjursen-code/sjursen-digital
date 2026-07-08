<#
.SYNOPSIS
    Startup and installer script for the Sjursen Digital Gateway.
.DESCRIPTION
    This script coordinates the installation of dependencies and starts the
    Gateway FastAPI backend and SvelteKit UI concurrently.
.PARAMETER install
    Installs pip and npm requirements before booting.
.EXAMPLE
    .\run.ps1 -Install
#>
param(
    [switch]$Install
)

$ErrorActionPreference = "Stop"
$MyDir = Split-Path -Parent $MyInvocation.MyCommand.Path

Write-Host "=========================================================" -ForegroundColor Cyan
Write-Host "             Gateway Developer Console                   " -ForegroundColor Cyan
Write-Host "=========================================================" -ForegroundColor Cyan

# Check if we are running on Windows (PowerShell 5.1 compatibility check)
$isWin = $IsWindows -or ($env:OS -like "*Windows*") -or ($null -ne $env:windir)

# Check if we should auto-trigger installation (if any dependencies are missing)
$hasVenv = Test-Path "$MyDir\api\venv"
$hasNodeModules = Test-Path "$MyDir\ui\node_modules"

if (-not $Install -and (-not $hasVenv -or -not $hasNodeModules)) {
    Write-Host "`nDependencies are not fully installed. Automatically running installation..." -ForegroundColor Yellow
    $Install = $true
}

# 1. Dependency installation block
if ($Install) {
    Write-Host "`n[1/2] Installing Python Gateway dependencies..." -ForegroundColor Yellow
    Push-Location "$MyDir\api"
    try {
        if (-not (Test-Path "venv")) {
            Write-Host "Creating Python virtual environment for Gateway..." -ForegroundColor DarkGray
            python -m venv venv
        }
        $pipPath = if ($isWin) { "venv\Scripts\pip.exe" } else { "venv/bin/pip" }
        & $pipPath install --upgrade pip
        & $pipPath install -r requirements.txt
        Write-Host "Gateway backend dependencies installed successfully." -ForegroundColor Green
    }
    catch {
        Write-Error "Failed to install Python dependencies for Gateway: $_"
        Pop-Location
        exit 1
    }
    Pop-Location

    Write-Host "`n[2/2] Installing SvelteKit Gateway UI dependencies..." -ForegroundColor Yellow
    Push-Location "$MyDir\ui"
    try {
        if ($isWin) { cmd.exe /c "npm install" } else { npm install }
        Write-Host "Gateway frontend dependencies installed successfully." -ForegroundColor Green
    }
    catch {
        Write-Error "Failed to install Node dependencies for Gateway: $_"
        Pop-Location
        exit 1
    }
    Pop-Location
    
    Write-Host "`nInstallation complete! Booting system..." -ForegroundColor Green
    Write-Host "---------------------------------------------------------" -ForegroundColor Gray
}

# 2. Process execution block
Write-Host "`nBooting Sjursen Digital gateway runtimes concurrently..." -ForegroundColor Cyan

# Define python executable
$gwPython = if (Test-Path "$MyDir\api\venv") { if ($isWin) { "$MyDir\api\venv\Scripts\python.exe" } else { "$MyDir\api\venv/bin/python" } } else { "python" }

# Setup process commands
$gwApiArgs = @("-m", "uvicorn", "app.main:app", "--reload", "--port", "8000")
$npmCmd = if ($isWin) { "cmd.exe" } else { "npm" }
$npmArgs = if ($isWin) { @("/c", "npm run dev") } else { @("run", "dev") }

Write-Host "Launching background runtimes..." -ForegroundColor DarkGray

function Start-Native([string]$FileName, [string]$Arguments, [string]$WorkingDirectory) {
    $info = New-Object System.Diagnostics.ProcessStartInfo
    $info.FileName = $FileName
    $info.Arguments = $Arguments
    $info.WorkingDirectory = $WorkingDirectory
    $info.UseShellExecute = $false
    return [System.Diagnostics.Process]::Start($info)
}

# 1. Gateway API (8000)
$gwApiProcess = Start-Native $gwPython ($gwApiArgs -join " ") "$MyDir\api"

# 2. Gateway Svelte UI (3000)
if ($isWin) {
    $gwUiProcess = Start-Native $npmCmd ($npmArgs -join " ") "$MyDir\ui"
} else {
    $gwUiProcess = Start-Native "npm" "run dev" "$MyDir\ui"
}

# Output runtime logs info
Write-Host "`nSystem is running!" -ForegroundColor Green
Write-Host "  - Gateway Launcher: http://localhost:3000" -ForegroundColor Gray
Write-Host "  - Gateway API Reverse Proxy: http://localhost:8000/docs" -ForegroundColor Gray
Write-Host "Press CTRL+C in this terminal window to stop all services.`n" -ForegroundColor Yellow

# Watch processes
try {
    while (-not $gwApiProcess.HasExited -and -not $gwUiProcess.HasExited) {
        Start-Sleep -Milliseconds 500
    }
}
finally {
    Write-Host "`nStopping background engines gracefully..." -ForegroundColor Yellow
    
    if ($gwApiProcess -and -not $gwApiProcess.HasExited) { try { $gwApiProcess.Kill() } catch {} }
    if ($gwUiProcess -and -not $gwUiProcess.HasExited) { try { $gwUiProcess.Kill() } catch {} }
    
    Write-Host "All processes terminated. Have a great day!" -ForegroundColor Green
}

<#
.SYNOPSIS
    Startup and installer script for the Komfyrvakt application.
.DESCRIPTION
    This script coordinates the installation of dependencies and starts both
    the FastAPI backend and the SvelteKit frontend concurrently.
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
Write-Host "             Komfyrvakt Developer Console                " -ForegroundColor Cyan
Write-Host "=========================================================" -ForegroundColor Cyan

# Check if we should auto-trigger installation (if no venv or node_modules exists)
$hasVenv = Test-Path "$MyDir\api\venv"
$hasNodeModules = Test-Path "$MyDir\ui\node_modules"

if (-not $Install -and (-not $hasVenv -or -not $hasNodeModules)) {
    Write-Host "`nDependencies are not fully installed. Automatically running installation..." -ForegroundColor Yellow
    $Install = $true
}

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
        if ($IsWindows) {
            cmd.exe /c "npm install"
        } else {
            npm install
        }
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
# Using the virtual environment's python directly is 100% bulletproof for loading correct site-packages!
if (Test-Path "$MyDir\api\venv") {
    if ($IsWindows) {
        $apiCmd = "$MyDir\api\venv\Scripts\python.exe"
    } else {
        $apiCmd = "$MyDir\api\venv/bin/python"
    }
    $apiArgs = @("-m", "uvicorn", "app.main:app", "--reload", "--port", "8000")
} else {
    $apiCmd = "python"
    $apiArgs = @("-m", "uvicorn", "app.main:app", "--reload", "--port", "8000")
}

# Run the SvelteKit development process via npm
if ($IsWindows) {
    $uiCmd = "cmd.exe"
    $uiArgs = @("/c", "npm run dev")
} else {
    $uiCmd = "npm"
    $uiArgs = @("run", "dev")
}

# Launching native processes instead of Start-Job. 
# This preserves PATH variables, user environments, and requires zero background job session contexts!
Write-Host "Launching background runtimes..." -ForegroundColor DarkGray

$apiStartInfo = New-Object System.Diagnostics.ProcessStartInfo
$apiStartInfo.FileName = $apiCmd
$apiStartInfo.Arguments = $apiArgs -join " "
$apiStartInfo.WorkingDirectory = "$MyDir\api"
$apiStartInfo.UseShellExecute = $false
$apiStartInfo.RedirectStandardOutput = $false
$apiStartInfo.RedirectStandardError = $false

$uiStartInfo = New-Object System.Diagnostics.ProcessStartInfo
$uiStartInfo.FileName = $uiCmd
$uiStartInfo.Arguments = $uiArgs -join " "
$uiStartInfo.WorkingDirectory = "$MyDir\ui"
$uiStartInfo.UseShellExecute = $false
$uiStartInfo.RedirectStandardOutput = $false
$uiStartInfo.RedirectStandardError = $false

$apiProcess = [System.Diagnostics.Process]::Start($apiStartInfo)
$uiProcess = [System.Diagnostics.Process]::Start($uiStartInfo)

# Register clean shutdown on interrupt (CTRL+C)
Write-Host "`nSystem is running!" -ForegroundColor Green
Write-Host "  - Frontend: http://localhost:3000" -ForegroundColor Gray
Write-Host "  - API Docs: http://localhost:8000/docs" -ForegroundColor Gray
Write-Host "Press CTRL+C in this terminal window to stop all services.`n" -ForegroundColor Yellow

# Watch both processes and wait for exit/interruption
try {
    while (-not $apiProcess.HasExited -and -not $uiProcess.HasExited) {
        Start-Sleep -Milliseconds 500
    }
}
finally {
    Write-Host "`nStopping background engines gracefully..." -ForegroundColor Yellow
    
    # Kill backend process
    if ($apiProcess -and -not $apiProcess.HasExited) {
        try {
            $apiProcess.Kill()
        } catch {}
    }
    
    # Kill frontend process
    if ($uiProcess -and -not $uiProcess.HasExited) {
        try {
            $uiProcess.Kill()
        } catch {}
    }
    
    Write-Host "All processes terminated. Have a great day!" -ForegroundColor Green
}

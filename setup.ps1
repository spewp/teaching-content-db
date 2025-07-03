# PowerShell setup script for Teaching Content Database

Write-Host "Setting up Teaching Content Database development environment..." -ForegroundColor Green
Write-Host ""

# Check if Python is installed
try {
    $pythonVersion = python --version 2>$null
    if ($LASTEXITCODE -ne 0) {
        throw "Python not found"
    }
    Write-Host "✓ Python found: $pythonVersion" -ForegroundColor Green
}
catch {
    Write-Host "Error: Python is not installed or not in PATH" -ForegroundColor Red
    Write-Host "Please install Python 3.8+ from https://python.org" -ForegroundColor Yellow
    Write-Host "Make sure to check 'Add Python to PATH' during installation" -ForegroundColor Yellow
    Read-Host "Press Enter to exit"
    exit 1
}

Write-Host ""

# Create virtual environment
Write-Host "Creating virtual environment..." -ForegroundColor Blue
try {
    python -m venv venv
    if ($LASTEXITCODE -ne 0) {
        throw "Failed to create virtual environment"
    }
    Write-Host "✓ Virtual environment created" -ForegroundColor Green
}
catch {
    Write-Host "Error: Failed to create virtual environment" -ForegroundColor Red
    Read-Host "Press Enter to exit"
    exit 1
}

Write-Host ""

# Activate virtual environment and install dependencies
Write-Host "Activating virtual environment and installing dependencies..." -ForegroundColor Blue
try {
    & "venv\Scripts\Activate.ps1"
    python -m pip install --upgrade pip
    pip install -r requirements.txt
    
    if ($LASTEXITCODE -ne 0) {
        throw "Failed to install dependencies"
    }
}
catch {
    Write-Host "Error: Failed to install dependencies" -ForegroundColor Red
    Read-Host "Press Enter to exit"
    exit 1
}

Write-Host ""
Write-Host "✅ Setup complete!" -ForegroundColor Green
Write-Host ""
Write-Host "To activate the virtual environment in the future, run:" -ForegroundColor Yellow
Write-Host "  venv\Scripts\Activate.ps1" -ForegroundColor Cyan
Write-Host ""
Write-Host "To deactivate, run:" -ForegroundColor Yellow
Write-Host "  deactivate" -ForegroundColor Cyan
Write-Host ""

Read-Host "Press Enter to continue" 
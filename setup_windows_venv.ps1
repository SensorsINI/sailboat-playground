# PowerShell version of the Windows setup script
# Run with: powershell -ExecutionPolicy Bypass -File setup_windows_venv.ps1

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "Sailboat Playground - Windows Setup (PowerShell)" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# Check if Python is installed
try {
    $pythonVersion = python --version 2>&1
    Write-Host "Python found: $pythonVersion" -ForegroundColor Green
} catch {
    Write-Host "ERROR: Python is not installed or not in PATH" -ForegroundColor Red
    Write-Host "Please install Python 3.7+ from https://python.org" -ForegroundColor Red
    Write-Host "Or use the Microsoft Store version" -ForegroundColor Red
    Read-Host "Press Enter to exit"
    exit 1
}

# Create virtual environment
Write-Host ""
Write-Host "Creating virtual environment..." -ForegroundColor Yellow
if (Test-Path ".venv_windows") {
    Write-Host "Virtual environment already exists. Removing old one..." -ForegroundColor Yellow
    Remove-Item -Recurse -Force ".venv_windows"
}

python -m venv .venv_windows
if ($LASTEXITCODE -ne 0) {
    Write-Host "ERROR: Failed to create virtual environment" -ForegroundColor Red
    Read-Host "Press Enter to exit"
    exit 1
}

Write-Host "Virtual environment created successfully!" -ForegroundColor Green

# Activate virtual environment
Write-Host ""
Write-Host "Activating virtual environment..." -ForegroundColor Yellow
& ".venv_windows\Scripts\Activate.ps1"

# Upgrade pip
Write-Host ""
Write-Host "Upgrading pip..." -ForegroundColor Yellow
python -m pip install --upgrade pip

# Install build tools
Write-Host ""
Write-Host "Installing build tools..." -ForegroundColor Yellow
pip install wheel setuptools

# Install requirements
Write-Host ""
Write-Host "Installing Python dependencies..." -ForegroundColor Yellow
pip install -r requirements.txt

# Install test requirements
Write-Host ""
Write-Host "Installing test dependencies..." -ForegroundColor Yellow
pip install -r test_requirements.txt

# Build Cython extensions
Write-Host ""
Write-Host "Building Cython extensions..." -ForegroundColor Yellow
python setup.py build_ext --inplace

Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "Setup Complete!" -ForegroundColor Green
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "To activate the virtual environment, run:" -ForegroundColor White
Write-Host "  .venv_windows\Scripts\Activate.ps1" -ForegroundColor Gray
Write-Host ""
Write-Host "To run examples:" -ForegroundColor White
Write-Host "  python examples\upwind\sailing_upwind.py" -ForegroundColor Gray
Write-Host "  python examples\downwind\sailing_downwind.py" -ForegroundColor Gray
Write-Host ""
Write-Host "To deactivate the virtual environment:" -ForegroundColor White
Write-Host "  deactivate" -ForegroundColor Gray
Write-Host ""
Read-Host "Press Enter to continue"




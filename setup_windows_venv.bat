@echo off
REM Windows Virtual Environment Setup for Sailboat Playground
REM This script creates a dedicated virtual environment for Windows execution

echo ========================================
echo Sailboat Playground - Windows Setup
echo ========================================
echo.

REM Check if Python is installed
python3.9 --version >nul 2>&1
if errorlevel 1 (
    python3.13 --version >nul 2>&1
    if errorlevel 1 (
        echo ERROR: Python is not installed or not in PATH
        echo Please install Python 3.7+ from https://python.org
        echo Or use the Microsoft Store version
        pause
        exit /b 1
    ) else (
        set PYTHON_CMD=python3.13
    )
) else (
    set PYTHON_CMD=python3.9
)

echo Python found:
%PYTHON_CMD% --version

REM Create virtual environment
echo.
echo Creating virtual environment...
if exist ".venv_windows" (
    echo Virtual environment already exists. Removing old one...
    rmdir /s /q ".venv_windows"
)

%PYTHON_CMD% -m venv .venv_windows
if errorlevel 1 (
    echo ERROR: Failed to create virtual environment
    pause
    exit /b 1
)

echo Virtual environment created successfully!

REM Activate virtual environment
echo.
echo Activating virtual environment...
call .venv_windows\Scripts\activate.bat

REM Upgrade pip
echo.
echo Upgrading pip...
%PYTHON_CMD% -m pip install --upgrade pip

REM Install build tools for Cython compilation
echo.
echo Installing build tools...
%PYTHON_CMD% -m pip install wheel setuptools

REM Install requirements
echo.
echo Installing Python dependencies...
%PYTHON_CMD% -m pip install -r requirements.txt

REM Install test requirements
echo.
echo Installing test dependencies...
%PYTHON_CMD% -m pip install -r test_requirements.txt

REM Build Cython extensions
echo.
echo Building Cython extensions...
%PYTHON_CMD% setup.py build_ext --inplace

echo.
echo ========================================
echo Setup Complete!
echo ========================================
echo.
echo To activate the virtual environment, run:
echo   .venv_windows\Scripts\activate.bat
echo.
echo To run examples:
echo   python examples\upwind\sailing_upwind.py
echo   python examples\downwind\sailing_downwind.py
echo.
echo To deactivate the virtual environment:
echo   deactivate
echo.
pause

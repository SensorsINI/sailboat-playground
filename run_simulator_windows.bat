@echo off
REM Windows version of the simulator runner
REM This script activates the Windows virtual environment and runs simulations

echo ========================================
echo Sailboat Playground - Windows Runner
echo ========================================
echo.

REM Check if virtual environment exists
if not exist ".venv_windows" (
    echo ERROR: Windows virtual environment not found!
    echo Please run setup_windows_venv.bat first
    pause
    exit /b 1
)

REM Activate virtual environment
echo Activating Windows virtual environment...
call .venv_windows\Scripts\activate.bat

REM Set Python path to include current directory
set PYTHONPATH=.

REM Check if arguments provided
if "%~1"=="" (
    echo No script specified. Available examples:
    echo   python examples\upwind\sailing_upwind.py
    echo   python examples\downwind\sailing_downwind.py
    echo.
    echo Usage: run_simulator_windows.bat [script_path]
    pause
    exit /b 0
)

REM Run the specified script
echo Running: %*
python %*

REM Keep window open if there was an error
if errorlevel 1 (
    echo.
    echo Script finished with errors.
    pause
)




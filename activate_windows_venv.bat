@echo off
REM Quick activation script for Windows virtual environment
echo Activating Sailboat Playground Windows Virtual Environment...
call .venv_windows\Scripts\activate.bat
echo Virtual environment activated!
echo.
echo Available commands:
echo   python examples\upwind\sailing_upwind.py
echo   python examples\downwind\sailing_downwind.py
echo   deactivate
echo.
cmd /k




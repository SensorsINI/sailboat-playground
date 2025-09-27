# Windows Virtual Environment Setup

This document explains how to set up a dedicated Windows virtual environment for the Sailboat Playground project.

## Quick Start

### Option 1: Batch Script (Recommended)
1. Open Command Prompt or PowerShell in the project directory
2. Run: `setup_windows_venv.bat`
3. Follow the prompts

### Option 2: PowerShell Script
1. Open PowerShell in the project directory
2. Run: `powershell -ExecutionPolicy Bypass -File setup_windows_venv.ps1`
3. Follow the prompts

## What Gets Installed

The setup script will:
- Create a virtual environment in `.venv_windows/`
- Install all required Python packages
- Compile Cython extensions for Windows
- Set up the environment for optimal performance

## Running Simulations

### Quick Activation
```batch
activate_windows_venv.bat
```

### Run Examples
```batch
# Using the runner script
run_simulator_windows.bat examples\upwind\sailing_upwind.py
run_simulator_windows.bat examples\downwind\sailing_downwind.py

# Or manually after activation
.venv_windows\Scripts\activate.bat
python examples\upwind\sailing_upwind.py
```

## Virtual Environment Structure

```
.venv_windows/
├── Scripts/           # Windows executables
│   ├── activate.bat   # Activation script
│   ├── python.exe     # Python interpreter
│   └── pip.exe        # Package installer
├── Lib/               # Python libraries
└── pyvenv.cfg         # Environment config
```

## Troubleshooting

### Python Not Found
- Ensure Python 3.7+ is installed
- Add Python to your system PATH
- Try using `py` instead of `python` in the scripts

### Cython Compilation Errors
- Ensure Visual Studio Build Tools are installed
- Try running: `pip install --upgrade setuptools wheel`
- Check that all dependencies are installed

### Pyglet Display Issues
- For headless environments, the visualization will be disabled
- Ensure your system supports OpenGL for graphics

### Permission Errors
- Run Command Prompt as Administrator
- Check that the Dropbox folder has write permissions

## Development Notes

- The virtual environment is separate from any system Python installation
- All compiled Cython extensions are Windows-specific
- The environment includes both runtime and development dependencies
- Test dependencies are installed for running the test suite

## Cleanup

To remove the Windows virtual environment:
```batch
rmdir /s /q .venv_windows
```

## Integration with IDE

Most IDEs can detect and use the virtual environment:
- **VS Code**: Select the Python interpreter in `.venv_windows/Scripts/python.exe`
- **PyCharm**: Add interpreter from `.venv_windows/Scripts/python.exe`
- **Cursor**: Use the same interpreter path




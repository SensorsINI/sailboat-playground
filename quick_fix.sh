#!/bin/bash
# Quick fix for conda/venv environment management

echo "🔧 Applying quick fix for environment management..."

# Add environment management functions to current shell
cat >> ~/.bashrc << 'EOF'

# Environment management functions
show_env_status() {
    echo "=== Environment Status ==="
    if [[ -n "$VIRTUAL_ENV" ]]; then
        echo "🐍 Virtual Environment: $VIRTUAL_ENV"
        echo "   Python: $(which python)"
        echo "   Version: $(python --version 2>&1)"
    elif [[ -n "$CONDA_DEFAULT_ENV" ]]; then
        echo "🐍 Conda Environment: $CONDA_DEFAULT_ENV"
        echo "   Python: $(which python)"
        echo "   Version: $(python --version 2>&1)"
    else
        echo "🐍 System Python: $(which python)"
        echo "   Version: $(python --version 2>&1)"
    fi
    echo "========================="
}

activate_venv() {
    if [ -d ".venv" ] && [ -f ".venv/bin/activate" ]; then
        if [[ -n "$CONDA_DEFAULT_ENV" ]]; then
            conda deactivate 2>/dev/null
        fi
        source .venv/bin/activate
        echo "✅ Virtual environment activated"
        show_env_status
    else
        echo "❌ No .venv directory found in current location"
        return 1
    fi
}

deactivate_all() {
    if [[ -n "$VIRTUAL_ENV" ]]; then
        deactivate 2>/dev/null
        echo "✅ Virtual environment deactivated"
    fi
    if [[ -n "$CONDA_DEFAULT_ENV" ]] && [[ "$CONDA_DEFAULT_ENV" != "base" ]]; then
        conda deactivate 2>/dev/null
        echo "✅ Conda environment deactivated"
    fi
    show_env_status
}

# Aliases
alias env-status='show_env_status'
alias env-venv='activate_venv'
alias env-deactivate='deactivate_all'

# Enhanced cd function
cd() {
    builtin cd "$@"
    
    # Auto-activate .venv if present
    if [ -d ".venv" ] && [ -f ".venv/bin/activate" ]; then
        if [[ "$VIRTUAL_ENV" != "$PWD/.venv" ]]; then
            if [[ -n "$CONDA_DEFAULT_ENV" ]]; then
                conda deactivate 2>/dev/null
            fi
            source .venv/bin/activate
        fi
    # Auto-activate .conda if present
    elif [ -d ".conda" ] && [ -f ".conda/bin/activate" ]; then
        if [[ "$CONDA_PREFIX" != "$PWD/.conda" ]]; then
            if [[ -n "$VIRTUAL_ENV" ]]; then
                deactivate 2>/dev/null
            fi
            conda activate "./.conda"
        fi
    # Deactivate if leaving project directory
    elif [[ -n "$VIRTUAL_ENV" ]] && [[ "$PWD" != "$(dirname "$VIRTUAL_ENV")"* ]]; then
        deactivate 2>/dev/null
    elif [[ -n "$CONDA_DEFAULT_ENV" ]] && [[ "$CONDA_DEFAULT_ENV" != "base" ]] && [[ "$PWD" != "$(dirname "$CONDA_PREFIX")"* ]]; then
        conda deactivate 2>/dev/null
    fi
}

EOF

echo "✅ Added environment management functions to ~/.bashrc"
echo ""
echo "🎉 Quick fix applied! To use:"
echo "   1. Run: source ~/.bashrc"
echo "   2. Or start a new terminal"
echo ""
echo "New commands available:"
echo "   env-status    - Show current environment"
echo "   env-venv      - Activate .venv in current directory"
echo "   env-deactivate - Deactivate all environments"
echo ""
echo "Auto-activation:"
echo "   - .venv directories will auto-activate when you cd into them"
echo "   - .conda directories will auto-activate when you cd into them"
echo "   - Environments will deactivate when you leave project directories"

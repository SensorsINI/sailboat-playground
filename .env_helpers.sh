#!/bin/bash
# Environment management helpers for conda and venv coexistence

# Function to detect and activate the appropriate environment
detect_and_activate_env() {
    local current_dir="$PWD"
    local env_activated=false
    
    # Check for .venv directory (Python virtual environment)
    if [ -d ".venv" ] && [ -f ".venv/bin/activate" ]; then
        if [[ "$VIRTUAL_ENV" != "$current_dir/.venv" ]]; then
            # Deactivate conda if active
            if [[ -n "$CONDA_DEFAULT_ENV" ]]; then
                conda deactivate 2>/dev/null
            fi
            # Activate virtual environment
            source .venv/bin/activate
            env_activated=true
        fi
    # Check for .conda directory (conda environment)
    elif [ -d ".conda" ] && [ -f ".conda/bin/activate" ]; then
        if [[ "$CONDA_PREFIX" != "$current_dir/.conda" ]]; then
            # Deactivate venv if active
            if [[ -n "$VIRTUAL_ENV" ]]; then
                deactivate 2>/dev/null
            fi
            # Activate conda environment
            conda activate "./.conda"
            env_activated=true
        fi
    # Check if we're leaving a project directory
    elif [[ -n "$VIRTUAL_ENV" ]] && [[ "$current_dir" != "$(dirname "$VIRTUAL_ENV")"* ]]; then
        # We're leaving a venv project directory
        deactivate 2>/dev/null
        env_activated=true
    elif [[ -n "$CONDA_DEFAULT_ENV" ]] && [[ "$CONDA_DEFAULT_ENV" != "base" ]] && [[ "$current_dir" != "$(dirname "$CONDA_PREFIX")"* ]]; then
        # We're leaving a conda project directory
        conda deactivate 2>/dev/null
        env_activated=true
    fi
    
    return 0
}

# Function to show current environment status
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

# Function to manually activate venv
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

# Function to manually activate conda
activate_conda() {
    if [ -d ".conda" ] && [ -f ".conda/bin/activate" ]; then
        if [[ -n "$VIRTUAL_ENV" ]]; then
            deactivate 2>/dev/null
        fi
        conda activate "./.conda"
        echo "✅ Conda environment activated"
        show_env_status
    else
        echo "❌ No .conda directory found in current location"
        return 1
    fi
}

# Function to deactivate all environments
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

# Export functions for use in bashrc
export -f detect_and_activate_env
export -f show_env_status
export -f activate_venv
export -f activate_conda
export -f deactivate_all

# Create aliases for easier access
alias env-status='show_env_status'
alias env-venv='activate_venv'
alias env-conda='activate_conda'
alias env-deactivate='deactivate_all'

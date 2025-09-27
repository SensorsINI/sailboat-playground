#!/bin/bash
# Script to safely update .bashrc with improved conda/venv handling

set -e

echo "🔧 Updating .bashrc with improved environment handling..."

# Create backup of current .bashrc
if [ -f ~/.bashrc ]; then
    cp ~/.bashrc ~/.bashrc.backup.$(date +%Y%m%d_%H%M%S)
    echo "✅ Created backup: ~/.bashrc.backup.$(date +%Y%m%d_%H%M%S)"
fi

# Copy the improved bashrc
cp .bashrc_improved ~/.bashrc
echo "✅ Updated ~/.bashrc with improved version"

# Make sure the environment helpers are executable
chmod +x .env_helpers.sh
echo "✅ Made .env_helpers.sh executable"

echo ""
echo "🎉 Update complete! To apply changes:"
echo "   1. Run: source ~/.bashrc"
echo "   2. Or start a new terminal session"
echo ""
echo "New environment management commands:"
echo "   env-status    - Show current environment status"
echo "   env-venv      - Manually activate .venv in current directory"
echo "   env-conda     - Manually activate .conda in current directory"
echo "   env-deactivate - Deactivate all environments"
echo ""
echo "The system will now automatically:"
echo "   - Detect .venv directories and activate them"
echo "   - Detect .conda directories and activate them"
echo "   - Switch between environments when changing directories"
echo "   - Show clear environment indicators in your prompt"

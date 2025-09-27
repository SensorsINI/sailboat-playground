#!/bin/bash
# Script to run sailboat playground simulations
# This sets up the environment and runs the simulation

# Activate virtual environment
source .venv/bin/activate

# Set Python path to include current directory
export PYTHONPATH=.

# Run the simulation
python "$@"

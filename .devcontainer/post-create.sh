#!/usr/bin/env bash
set -euo pipefail

echo "========================================"
echo "Setting up Agentic Travel Challenge..."
echo "========================================"

python -m pip install --upgrade pip

# Install the course project and core dependencies
python -m pip install -e '.[protocols]'

# Jupyter environment
python -m pip install \
  'jupyterlab>=4,<5' \
  'ipykernel>=6,<7'

echo
echo "Running instructor scaffold checks (student tasks are not implemented)..."
python -m pytest -q -m scaffold

echo
echo "========================================"
echo "Setup complete."
echo
echo "Start here:"
echo "notebooks/student/01_Week1_Contracts_and_Baseline.ipynb"
echo "========================================"

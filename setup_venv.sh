#!/usr/bin/env bash
set -e

# Create venv if missing
if [ ! -d "venv" ]; then
  echo "Creating virtual environment..."
  python3 -m venv venv
else
  echo "Virtual environment already exists."
fi

# Activate and install
# shellcheck source=/dev/null
source venv/bin/activate

echo "Upgrading pip..."
python -m pip install --upgrade pip

echo "Installing requirements..."
pip install -r "$(dirname "$0")/requirements.txt"

echo
echo "Done. To activate the environment later, run:"
echo "  source venv/bin/activate"

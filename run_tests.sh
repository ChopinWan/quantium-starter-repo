#!/usr/bin/env bash

set -u

activate_script=""

if [[ -f "venv/bin/activate" ]]; then
  activate_script="venv/bin/activate"
elif [[ -f "venv/Scripts/activate" ]]; then
  activate_script="venv/Scripts/activate"
elif [[ -f ".venv/bin/activate" ]]; then
  activate_script=".venv/bin/activate"
elif [[ -f ".venv/Scripts/activate" ]]; then
  activate_script=".venv/Scripts/activate"
fi

if [[ -z "$activate_script" ]]; then
  echo "Error: could not find a virtual environment activation script."
  exit 1
fi

# shellcheck disable=SC1090
source "$activate_script" || {
  echo "Error: failed to activate virtual environment."
  exit 1
}

python -m pytest -q
pytest_status=$?

if [[ $pytest_status -eq 0 ]]; then
  echo "Test suite passed."
  exit 0
fi

echo "Test suite failed."
exit 1

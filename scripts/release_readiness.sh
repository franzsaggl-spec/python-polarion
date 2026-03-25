#!/usr/bin/env bash
set -euo pipefail

python -m pip install --upgrade pip >/dev/null
pip install -e ".[test]" >/dev/null
pip install build twine ruff >/dev/null

ruff check .
ruff format --check .
pytest tests/ -q

python -m build
python -m twine check dist/*

echo "release-readiness: OK"

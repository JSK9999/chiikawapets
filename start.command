#!/bin/bash
# Double-click launcher for macOS. First run creates .venv and installs PySide6.
set -euo pipefail
cd "$(dirname "$0")"
if ! command -v python3 >/dev/null 2>&1; then
  echo 'Python 3가 필요합니다: https://www.python.org/downloads/'
  read -r -p 'Enter를 누르면 종료합니다...'
  exit 1
fi
[ -d .venv ] || python3 -m venv .venv
# shellcheck disable=SC1091
source .venv/bin/activate
python -c 'import PySide6' 2>/dev/null || python -m pip install -q -r requirements.txt
exec python main.py

#!/bin/bash
# Builds dist/ChiikawaPets.app (unsigned, personal use). Requires: pip install pyinstaller
set -euo pipefail
cd "$(dirname "$0")"
source .venv/bin/activate
python -c 'import PyInstaller' 2>/dev/null || python -m pip install -q pyinstaller
rm -rf build dist
pyinstaller --noconfirm --clean ChiikawaPets.spec
echo "완료: $(pwd)/dist/ChiikawaPets.app"
echo "처음 열 때 Gatekeeper가 막으면: 우클릭 > 열기, 또는 xattr -dr com.apple.quarantine dist/ChiikawaPets.app"

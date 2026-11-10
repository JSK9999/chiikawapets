#!/bin/bash
# Double-click (or ./start.command). First run: creates .venv, installs PySide6,
# downloads character images for personal use. Afterwards it just launches.
set -euo pipefail
cd "$(dirname "$0")"
if ! command -v python3 >/dev/null 2>&1; then
  echo 'Python 3가 필요합니다: https://www.python.org/downloads/'
  read -r -p 'Enter를 누르면 종료합니다...'
  exit 1
fi
if [ ! -d .venv ]; then
  echo '[1/3] 가상환경 만드는 중...'
  python3 -m venv .venv
fi
# shellcheck disable=SC1091
source .venv/bin/activate
if ! python -c 'import PySide6' 2>/dev/null; then
  echo '[2/3] PySide6 설치 중 (1분 정도)...'
  python -m pip install -q -r requirements.txt
fi
echo '[3/3] 캐릭터 이미지 확인 중...'
python scripts/download_assets.py
echo '펫을 띄웁니다. 종료는 캐릭터 우클릭 > 종료'
exec python main.py

"""Download spritesheets from the reference repo to this machine only.

The reference project forbids redistribution, so assets are never bundled or
committed; each user fetches them for personal use.
"""
from __future__ import annotations

import json
import urllib.request
from collections.abc import Callable
from pathlib import Path

from .catalog import CHARACTERS, GENERATED, RAW_BASE, REPO_URL

PNG_MAGIC = b"\x89PNG\r\n\x1a\n"
FILES = ("pet.json", "spritesheet.png")
Progress = Callable[[str, int, int], None]


def _fetch(url: str) -> bytes:
    request = urllib.request.Request(url, headers={"User-Agent": "ChiikawaPets-Personal/1.0"})
    with urllib.request.urlopen(request, timeout=30) as response:
        return response.read()


def _validate(name: str, data: bytes) -> None:
    if name.endswith(".png"):
        if not data.startswith(PNG_MAGIC):
            raise ValueError("PNG 형식이 아닙니다")
    else:
        parsed = json.loads(data.decode("utf-8"))
        if not isinstance(parsed, dict) or "id" not in parsed:
            raise ValueError("pet.json 형식이 아닙니다")


def downloadable() -> list[str]:
    return [k for k in CHARACTERS if k not in GENERATED]


def missing(root: Path, keys: list[str] | None = None) -> list[str]:
    keys = keys or downloadable()
    return [k for k in keys if k not in GENERATED and not (root / k / "spritesheet.png").is_file()]


def download(root: Path, keys: list[str] | None = None, progress: Progress | None = None) -> list[str]:
    """Download missing pets into root. Returns a list of error strings."""
    keys = keys or downloadable()
    errors: list[str] = []
    total = len(keys) * len(FILES)
    done = 0
    for key in keys:
        if key not in CHARACTERS or key in GENERATED:
            errors.append(f"{key}: 다운로드 대상이 아닙니다")
            continue
        folder = root / key
        folder.mkdir(parents=True, exist_ok=True)
        for name in FILES:
            done += 1
            target = folder / name
            if progress:
                progress(f"{CHARACTERS[key]} / {name}", done, total)
            if target.is_file() and target.stat().st_size > 0:
                continue
            try:
                data = _fetch(f"{RAW_BASE}/{key}/{name}")
                _validate(name, data)
                target.write_bytes(data)
            except Exception as exc:  # noqa: BLE001 - report and keep going
                errors.append(f"{key}/{name}: {exc}")
    return errors


def main() -> int:
    from .paths import assets_dir

    root = assets_dir()
    print(f"원본: {REPO_URL}")
    print("원작자의 이용 안내(비상업, 재배포 금지)를 존중해 개인용으로만 사용하세요.")
    print(f"저장 위치: {root}")
    errors = download(root, progress=lambda label, i, n: print(f"[{i}/{n}] {label}"))
    if errors:
        print("일부 실패:\n  " + "\n  ".join(errors))
        return 1
    print("완료")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

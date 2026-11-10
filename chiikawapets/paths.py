"""Where assets and config live. Nothing here touches the network."""
from __future__ import annotations

import os
import sys
from pathlib import Path

APP_NAME = "ChiikawaPets"


def support_dir() -> Path:
    base = Path.home() / "Library" / "Application Support" if sys.platform == "darwin" else Path.home() / ".config"
    path = base / APP_NAME
    path.mkdir(parents=True, exist_ok=True)
    return path


def config_path() -> Path:
    return support_dir() / "config.json"


def repo_assets_dir() -> Path:
    return Path(__file__).resolve().parent.parent / "assets" / "pets"


def assets_dir() -> Path:
    """Resolution order: env override, repo checkout, Application Support."""
    override = os.environ.get("CHIIKAWA_ASSETS")
    if override:
        return Path(override).expanduser()
    repo = repo_assets_dir()
    if (repo / "chiikawa" / "spritesheet.png").is_file():
        return repo
    return support_dir() / "pets"


def sheet_path(key: str, root: Path | None = None) -> Path:
    return (root or assets_dir()) / key / "spritesheet.png"

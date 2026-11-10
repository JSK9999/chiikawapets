"""Persisted user settings with validation of everything read from disk."""
from __future__ import annotations

import json
from dataclasses import dataclass, field

from .catalog import CHARACTERS, DEFAULT_PETS
from .paths import config_path

MIN_HEIGHT, MAX_HEIGHT = 48, 400


@dataclass
class Config:
    pets: list[str] = field(default_factory=lambda: list(DEFAULT_PETS))
    height: int = 128
    all_spaces: bool = True

    @classmethod
    def load(cls) -> "Config":
        path = config_path()
        if not path.is_file():
            return cls()
        try:
            raw = json.loads(path.read_text("utf-8"))
        except (OSError, ValueError):
            return cls()
        return cls.from_dict(raw if isinstance(raw, dict) else {})

    @classmethod
    def from_dict(cls, raw: dict) -> "Config":
        cfg = cls()
        pets = raw.get("pets")
        if isinstance(pets, list):
            valid = [p for p in pets if isinstance(p, str) and p in CHARACTERS]
            if valid:
                cfg.pets = valid
        height = raw.get("height")
        if isinstance(height, int) and MIN_HEIGHT <= height <= MAX_HEIGHT:
            cfg.height = height
        if isinstance(raw.get("all_spaces"), bool):
            cfg.all_spaces = raw["all_spaces"]
        return cfg

    def save(self) -> None:
        data = {"pets": self.pets, "height": self.height, "all_spaces": self.all_spaces}
        try:
            config_path().write_text(json.dumps(data, ensure_ascii=False, indent=2), "utf-8")
        except OSError:
            pass

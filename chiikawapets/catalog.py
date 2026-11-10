"""Static catalog: character ids, display names, spritesheet layout."""
from __future__ import annotations

REPO_URL = "https://github.com/heelee912/chiikawa-dots-pets"
RAW_BASE = "https://raw.githubusercontent.com/heelee912/chiikawa-dots-pets/main/pets"

CHARACTERS: dict[str, str] = {
    "chiikawa": "치이카와",
    "hachiware": "하치와레",
    "usagi": "우사기",
    "momonga": "모몽가",
    "shisa": "시사",
    "rakko": "랏코",
    "kurimanju": "쿠리만주",
    "siren": "세이렌",
    "furuhonya": "후루혼야",
    "anoko": "아노코",
    "dekatsuyo": "데카츠요",
    "pajama-green": "파자마 파티즈 (초록)",
    "pajama-pink": "파자마 파티즈 (분홍)",
    "pajama-purple": "파자마 파티즈 (보라)",
    "pajama-white": "파자마 파티즈 (흰색)",
}
# Drawn locally by chiikawapets.pajama instead of downloaded from the reference repo.
GENERATED = {"pajama-green", "pajama-pink", "pajama-purple", "pajama-white"}
DEFAULT_PETS = ["chiikawa", "hachiware", "usagi"]

# Codex pet spritesheet v2: 8 columns, 192x208 cells, 1536x2288 PNG.
SHEET_W, SHEET_H = 1536, 2288
CELL_W, CELL_H = 192, 208
COLS = 8

# state -> (first row, frame count, frame duration ms). Durations follow the
# reference GIFs so motion speed matches the original.
STATES: dict[str, tuple[int, int, int]] = {
    "idle": (0, 6, 280),
    "running-right": (1, 8, 120),
    "running-left": (2, 8, 120),
    "waving": (3, 4, 140),
    "jumping": (4, 5, 140),
    "failed": (5, 8, 140),
    "waiting": (6, 6, 150),
    "running": (7, 6, 120),
    "review": (8, 6, 200),
    "look": (9, 16, 0),  # 16 gaze directions, clockwise from 12 o'clock
}

# Extra rows used only by the locally drawn Pajama Partys sheets (14 rows tall).
# They reproduce the group's own routine: hand-on-cheek bounce, arms up, spin.
DANCE_STATES: dict[str, tuple[int, int, int]] = {
    "dance-point": (11, 8, 110),
    "dance-up": (12, 6, 120),
    "dance-spin": (13, 8, 90),
    "dance-shake": (14, 8, 90),  # the signature move: back turned, hips swinging
}
ALL_STATES: dict[str, tuple[int, int, int]] = {**STATES, **DANCE_STATES}
DANCE_SHEET_H = CELL_H * 15

SIZE_PRESETS: dict[str, int] = {"작게": 96, "보통": 128, "크게": 160, "아주 크게": 208}

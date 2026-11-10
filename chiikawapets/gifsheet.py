"""Build a 15-row spritesheet from one looping character GIF.

The GIF loop is resampled into the four dance rows in order, so the real dance
plays back continuously. Every other state borrows frames from that set.
"""
from __future__ import annotations

from collections.abc import Callable
from pathlib import Path

from PySide6.QtCore import QRectF, Qt
from PySide6.QtGui import QImage, QImageReader, QPainter, qAlpha

from .catalog import ALL_STATES, CELL_H, CELL_W, COLS, DANCE_SHEET_H, DANCE_STATES, SHEET_W
from .gifcut import HueRanges, bounding_box, cut_character

FOOT_Y = 200  # sprite bottom inside the cell, matching the reference sheets
FLIPPED = {"running-left"}
Progress = Callable[[str, int, int], None]


def read_gif(path: Path) -> tuple[list[QImage], list[int]]:
    reader = QImageReader(str(path))
    frames, delays = [], []
    while True:
        frame = reader.read()
        if frame.isNull():
            break
        frames.append(frame)
        delays.append(max(reader.nextImageDelay(), 10))
    if not frames:
        raise ValueError(f"GIF를 읽지 못했습니다: {path}")
    return frames, delays


def resample_indices(delays: list[int], count: int) -> list[int]:
    """Pick `count` source frames evenly spaced in time across the loop."""
    total = sum(delays)
    starts, acc = [], 0
    for d in delays:
        starts.append(acc)
        acc += d
    out = []
    for i in range(count):
        t = total * i / count
        idx = max(j for j, s in enumerate(starts) if s <= t)
        out.append(idx)
    return out


def _widths(images: list[QImage]) -> list[int]:
    widths = []
    for im in images:
        cols = [x for x in range(im.width()) if any(qAlpha(im.pixel(x, y)) for y in range(0, im.height(), 3))]
        widths.append((max(cols) - min(cols)) if cols else 0)
    return widths


def widest(images: list[QImage], count: int) -> list[int]:
    """Indices of the `count` widest frames (arms out), in time order."""
    widths = _widths(images)
    return sorted(sorted(range(len(images)), key=lambda i: -widths[i])[:count])


def narrowest(images: list[QImage], count: int) -> list[int]:
    """Indices of the `count` narrowest frames (arms in, standing), in time order."""
    widths = _widths(images)
    return sorted(sorted(range(len(images)), key=lambda i: widths[i])[:count])


def state_frames(dance: list[QImage]) -> dict[str, list[QImage]]:
    """Map every sheet state onto the resampled dance frames."""
    n = len(dance)
    even = lambda count: [dance[(i * n) // count] for i in range(count)]  # noqa: E731
    standing = [dance[i] for i in narrowest(dance, 6)]
    waving_idx = widest(dance, 4)
    frames = {
        "idle": standing,
        "running-right": even(8),
        "running-left": even(8),  # mirrored when drawn
        "waving": [dance[i] for i in waving_idx],
        "jumping": even(5),
        "failed": even(8),
        "waiting": even(6),
        "running": even(6),
        "review": even(6),
        "look": [standing[0]] * 16,
    }
    cursor = 0
    for state, (_, count, _) in DANCE_STATES.items():
        frames[state] = dance[cursor : cursor + count]
        cursor += count
    return frames


def build_sheet(gif: Path, out: Path, hues: HueRanges, dark: int = 110, progress: Progress | None = None) -> Path:
    frames, delays = read_gif(gif)
    dance_count = sum(count for _, count, _ in DANCE_STATES.values())
    picks = resample_indices(delays, dance_count)
    cuts: dict[int, QImage] = {}
    for n, idx in enumerate(sorted(set(picks))):
        if progress:
            progress(f"{gif.name}: 배경 제거 {n + 1}/{len(set(picks))}", n + 1, len(set(picks)))
        cuts[idx] = cut_character(frames[idx], hues, dark)
    dance = [cuts[i] for i in picks]
    x0, y0, x1, y1 = bounding_box(list(cuts.values()))
    src_w, src_h = x1 - x0 + 1, y1 - y0 + 1
    scale = min((CELL_W - 12) / src_w, (CELL_H - 12) / src_h)
    dst_w, dst_h = src_w * scale, src_h * scale
    sheet = QImage(SHEET_W, DANCE_SHEET_H, QImage.Format.Format_ARGB32_Premultiplied)
    sheet.fill(Qt.GlobalColor.transparent)
    painter = QPainter(sheet)
    painter.setRenderHint(QPainter.RenderHint.SmoothPixmapTransform)
    for state, images in state_frames(dance).items():
        row = ALL_STATES[state][0]
        for i, im in enumerate(images):
            col, r = i % COLS, row + i // COLS
            target = QRectF(col * CELL_W + (CELL_W - dst_w) / 2, r * CELL_H + FOOT_Y - dst_h, dst_w, dst_h)
            crop = im.copy(x0, y0, src_w, src_h)
            if state in FLIPPED:
                crop = crop.mirrored(True, False)
            painter.drawImage(target, crop)
    painter.end()
    out.parent.mkdir(parents=True, exist_ok=True)
    sheet.save(str(out))
    return out

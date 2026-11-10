"""Spritesheet loading: one transparent PNG -> per-state pixmap frames."""
from __future__ import annotations

import math
from pathlib import Path

from PySide6.QtCore import QPoint, QRect, QSize, Qt
from PySide6.QtGui import QImage, QPixmap

from .catalog import ALL_STATES, CELL_H, CELL_W, COLS, SHEET_H, SHEET_W


class SpriteSheet:
    """Frames for one character at one on-screen height and device pixel ratio."""

    def __init__(self, path: Path, height: int, dpr: float = 1.0):
        image = QImage(str(path))
        if image.isNull() or image.width() != SHEET_W or image.height() < SHEET_H or image.height() % CELL_H:
            raise ValueError(f"스프라이트시트 형식이 아닙니다: {path}")
        image = image.convertToFormat(QImage.Format.Format_ARGB32_Premultiplied)
        self.dpr = dpr
        self.size = QSize(round(CELL_W * height / CELL_H), height)
        target = QSize(round(self.size.width() * dpr), round(self.size.height() * dpr))
        rows = image.height() // CELL_H
        self.frames: dict[str, list[QPixmap]] = {
            state: self._slice(image, row, count, target)
            for state, (row, count, _) in ALL_STATES.items()
            if row + (count - 1) // COLS < rows
        }

    def _slice(self, image: QImage, row: int, count: int, target: QSize) -> list[QPixmap]:
        frames = []
        for i in range(count):
            col, r = i % COLS, row + i // COLS
            cell = image.copy(QRect(col * CELL_W, r * CELL_H, CELL_W, CELL_H))
            scaled = cell.scaled(target, Qt.AspectRatioMode.IgnoreAspectRatio, Qt.TransformationMode.SmoothTransformation)
            pixmap = QPixmap.fromImage(scaled)
            pixmap.setDevicePixelRatio(self.dpr)
            frames.append(pixmap)
        return frames

    def frame(self, state: str, index: int) -> QPixmap:
        frames = self.frames.get(state) or self.frames["idle"]
        return frames[index % len(frames)]

    def frame_count(self, state: str) -> int:
        return len(self.frames.get(state) or self.frames["idle"])

    def hit(self, state: str, index: int, pos: QPoint) -> bool:
        """True when pos (widget coords) lands on an opaque pixel."""
        pixmap = self.frame(state, index)
        x, y = int(pos.x() * self.dpr), int(pos.y() * self.dpr)
        if not (0 <= x < pixmap.width() and 0 <= y < pixmap.height()):
            return False
        return pixmap.toImage().pixelColor(x, y).alpha() > 40


def gaze_index(dx: float, dy: float) -> int:
    """0..15 clockwise from 12 o'clock, matching the 'look' row layout."""
    degrees = math.degrees(math.atan2(dx, -dy)) % 360.0
    return round(degrees / 22.5) % 16

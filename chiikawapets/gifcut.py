"""Cut one outlined character out of a frame: costume colour + outline-enclosed regions.

Works for Nagano-style art: a closed dark outline around pastel fills. Background
is whatever the border flood reaches; the character is the largest connected blob
of (costume-coloured pixels + outline-enclosed pixels + their outline) near the centre.
"""
from __future__ import annotations

from collections import deque

from PySide6.QtGui import QImage, qAlpha

HueRanges = tuple[tuple[float, float], ...]


def _hue(r: int, g: int, b: int) -> float:
    mx, mn = max(r, g, b), min(r, g, b)
    d = mx - mn
    if d == 0:
        return 0.0
    if mx == r:
        return (60 * ((g - b) / d)) % 360
    if mx == g:
        return 60 * ((b - r) / d) + 120
    return 60 * ((r - g) / d) + 240


def _classify(img: QImage, hues: HueRanges, dark: int, min_sat: float) -> tuple[bytearray, bytearray]:
    w, h = img.width(), img.height()
    buf, stride = bytes(img.constBits()), img.bytesPerLine()
    wall, colour = bytearray(w * h), bytearray(w * h)
    for y in range(h):
        row = y * stride
        for x in range(w):
            i = row + x * 4
            b, g, r = buf[i], buf[i + 1], buf[i + 2]
            k = y * w + x
            if (r * 299 + g * 587 + b * 114) // 1000 < dark:
                wall[k] = 1
                continue
            mx = max(r, g, b)
            if mx and (mx - min(r, g, b)) / mx >= min_sat:
                hue = _hue(r, g, b)
                if any(lo <= hue <= hi for lo, hi in hues):
                    colour[k] = 1
    return wall, colour


def _neighbours(k: int, w: int, h: int):
    x, y = k % w, k // w
    if x + 1 < w:
        yield k + 1
    if x > 0:
        yield k - 1
    if y + 1 < h:
        yield k + w
    if y > 0:
        yield k - w


def _flood(w: int, h: int, passable: bytearray, seeds) -> bytearray:
    seen, queue = bytearray(w * h), deque()
    for k in seeds:
        if passable[k] and not seen[k]:
            seen[k] = 1
            queue.append(k)
    while queue:
        k = queue.popleft()
        for nk in _neighbours(k, w, h):
            if passable[nk] and not seen[nk]:
                seen[nk] = 1
                queue.append(nk)
    return seen


def cut_character(frame: QImage, hues: HueRanges, dark: int = 110, min_sat: float = 0.28, halo: int = 4) -> QImage:
    """Return an ARGB32 image containing only the character (transparent elsewhere)."""
    img = frame.convertToFormat(QImage.Format.Format_ARGB32)
    w, h = img.width(), img.height()
    wall, colour = _classify(img, hues, dark, min_sat)
    open_px = bytearray(1 - v for v in wall)
    border = [*range(w), *range((h - 1) * w, h * w), *range(0, h * w, w), *range(w - 1, h * w, w)]
    background = _flood(w, h, open_px, border)
    candidate = bytearray(1 if (colour[k] or wall[k] or not background[k]) else 0 for k in range(w * h))
    best: bytearray = bytearray(w * h)
    best_size = 0
    seen = bytearray(w * h)
    for sy in range(h // 2 - 40, h // 2 + 60, 4):
        for sx in range(w // 2 - 60, w // 2 + 60, 4):
            k = sy * w + sx
            if not colour[k] or seen[k]:
                continue
            comp = _flood(w, h, candidate, [k])
            size = sum(comp)
            for j in range(w * h):
                if comp[j]:
                    seen[j] = 1
            if size > best_size:
                best, best_size = comp, size
    # keep outline only within `halo` px of the character's filled pixels
    core = bytearray(1 if (best[k] and not wall[k]) else 0 for k in range(w * h))
    grown = bytearray(core)
    for _ in range(halo):
        step = bytearray(grown)
        for k in range(w * h):
            if grown[k]:
                for nk in _neighbours(k, w, h):
                    if wall[nk]:
                        step[nk] = 1
        grown = step
    out = QImage(w, h, QImage.Format.Format_ARGB32)
    out.fill(0)
    for k in range(w * h):
        if grown[k] and best[k]:
            out.setPixel(k % w, k // w, img.pixel(k % w, k // w))
    return out


def bounding_box(images: list[QImage]) -> tuple[int, int, int, int]:
    """(x0, y0, x1, y1) inclusive, over every opaque pixel of every image."""
    x0, y0, x1, y1 = 10**9, 10**9, -1, -1
    for im in images:
        for y in range(im.height()):
            for x in range(im.width()):
                if qAlpha(im.pixel(x, y)):
                    x0, y0, x1, y1 = min(x0, x), min(y0, y), max(x1, x), max(y1, y)
    if x1 < 0:
        raise ValueError("캐릭터를 찾지 못했습니다")
    return x0, y0, x1, y1

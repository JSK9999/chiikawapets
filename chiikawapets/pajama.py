"""Generate Pajama Partys spritesheets (original fan drawings, Codex v2 layout).

The reference repo has no Pajama Partys, so the four members are drawn here with
QPainter in the same visual style: thick brown outline, pastel fill, big round body.
They are faceless: the hood opening is a dark grey disc with blush strokes.
"""
from __future__ import annotations

import json
import math
from dataclasses import dataclass, field
from pathlib import Path

from PySide6.QtCore import QPointF, QRectF, Qt
from PySide6.QtGui import QBrush, QColor, QImage, QPainter, QPainterPath, QPen

from .catalog import CELL_H, CELL_W, COLS, SHEET_H, SHEET_W, STATES

OUTLINE = QColor("#3a2a27")
FACE = QColor("#5b6b67")
BLUSH = QColor("#2d3936")
SWEAT = QColor("#8fc7f0")
LINE = 5.0

MEMBERS: dict[str, dict] = {
    "pajama-green": {"name": "파자마 파티즈 (초록)", "fill": "#c3e2ab", "shade": "#a9cf8e", "ears": "bumps", "tail": True},
    "pajama-pink": {"name": "파자마 파티즈 (분홍)", "fill": "#f7c3cf", "shade": "#eba6b6", "ears": "round", "tail": False},
    "pajama-purple": {"name": "파자마 파티즈 (보라)", "fill": "#d2c6e8", "shade": "#b9a9d8", "ears": "tall", "tail": False},
    "pajama-white": {"name": "파자마 파티즈 (흰색)", "fill": "#f6f3ec", "shade": "#e3ddd0", "ears": "horn", "tail": False},
}


@dataclass
class Pose:
    dx: float = 0.0
    dy: float = 0.0
    sx: float = 1.0
    sy: float = 1.0
    tilt: float = 0.0  # degrees, positive leans right
    arm_l: float = 0.0  # degrees raised from hanging position
    arm_r: float = 0.0
    foot_l: float = 0.0  # lift in px
    foot_r: float = 0.0
    face: tuple[float, float] = (0.0, 0.0)
    sweat: bool = False
    marks: str = "blush"  # blush | x
    flip: bool = False
    extra: dict = field(default_factory=dict)


# ----- pose generators --------------------------------------------------------
def _idle(i: int, n: int) -> Pose:
    t = 2 * math.pi * i / n
    return Pose(dy=-3 * math.sin(t), sy=1 + 0.02 * math.sin(t), sx=1 - 0.02 * math.sin(t))


def _run(i: int, n: int, flip: bool) -> Pose:
    t = 2 * math.pi * i / n
    s = math.sin(t)
    return Pose(dy=-9 * abs(s), tilt=9, arm_l=28 * s, arm_r=-28 * s, foot_r=7 * max(0.0, s), foot_l=7 * max(0.0, -s), flip=flip)


def _wave(i: int, n: int) -> Pose:
    return Pose(arm_r=150 + 22 * math.sin(2 * math.pi * i / n), tilt=-3, face=(2, 0))


def _jump(i: int, n: int) -> Pose:
    table = [
        Pose(dy=6, sx=1.1, sy=0.88),
        Pose(dy=-24, sx=0.94, sy=1.1, arm_l=60, arm_r=60),
        Pose(dy=-38, arm_l=140, arm_r=140, foot_l=4, foot_r=4),
        Pose(dy=-18, sy=1.04, arm_l=90, arm_r=90),
        Pose(dy=5, sx=1.08, sy=0.9),
    ]
    return table[i % len(table)]


def _failed(i: int, n: int) -> Pose:
    return Pose(dx=3 if i % 2 else -3, sy=0.97, sweat=True, marks="x", face=(0, 3))


def _wait(i: int, n: int) -> Pose:
    t = 2 * math.pi * i / n
    return Pose(tilt=5 * math.sin(t), face=(3 * math.sin(t), 0))


def _dance(i: int, n: int) -> Pose:
    t = 2 * math.pi * i / n
    up = 125 if i % 2 == 0 else 20
    return Pose(dy=-7 * abs(math.sin(t)), tilt=10 * math.sin(t), arm_l=up, arm_r=up, foot_l=3 * (i % 2), foot_r=3 * ((i + 1) % 2))


def _review(i: int, n: int) -> Pose:
    return Pose(dy=2 * math.sin(2 * math.pi * i / n), face=(0, 4), arm_r=70)


def _look(i: int, n: int) -> Pose:
    a = math.radians(i * 22.5)
    return Pose(face=(7 * math.sin(a), -6 * math.cos(a)))


GENERATORS = {
    "idle": _idle,
    "running-right": lambda i, n: _run(i, n, False),
    "running-left": lambda i, n: _run(i, n, True),
    "waving": _wave,
    "jumping": _jump,
    "failed": _failed,
    "waiting": _wait,
    "running": _dance,
    "review": _review,
    "look": _look,
}


# ----- drawing ----------------------------------------------------------------
class PajamaPainter:
    def __init__(self, member: dict):
        self.fill = QColor(member["fill"])
        self.shade = QColor(member["shade"])
        self.ears = member["ears"]
        self.tail = member["tail"]

    def draw(self, p: QPainter, pose: Pose) -> None:
        p.save()
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        p.translate(CELL_W / 2 + pose.dx, 196 + pose.dy)  # pivot at the feet
        if pose.flip:
            p.scale(-1, 1)
        p.rotate(pose.tilt)
        p.scale(pose.sx, pose.sy)
        p.setPen(QPen(OUTLINE, LINE, Qt.PenStyle.SolidLine, Qt.PenCapStyle.RoundCap, Qt.PenJoinStyle.RoundJoin))
        if self.tail:
            self._tail(p)
        self._feet(p, pose)
        self._ears(p)
        self._body(p)
        self._face(p, pose)
        self._buttons(p)
        self._arm(p, -58, -46, pose.arm_l, left=True)
        self._arm(p, 58, -46, pose.arm_r, left=False)
        if pose.sweat:
            self._sweat(p)
        p.restore()

    def _body(self, p: QPainter) -> None:
        p.setBrush(QBrush(self.fill))
        path = QPainterPath()
        path.addEllipse(QRectF(-67, -134, 134, 132))
        p.drawPath(path)

    def _face(self, p: QPainter, pose: Pose) -> None:
        fx, fy = pose.face
        centre = QPointF(fx, -84 + fy)
        p.setBrush(QBrush(FACE))
        p.drawEllipse(centre, 51, 49)
        pen = QPen(BLUSH, 3.5, Qt.PenStyle.SolidLine, Qt.PenCapStyle.RoundCap)
        p.setPen(pen)
        for side in (-1, 1):
            cx = fx + side * 26
            cy = -76 + fy
            if pose.marks == "x":
                p.drawLine(QPointF(cx - 6, cy - 6), QPointF(cx + 6, cy + 6))
                p.drawLine(QPointF(cx - 6, cy + 6), QPointF(cx + 6, cy - 6))
            else:
                for k in (-1, 0, 1):
                    x = cx + k * 7
                    p.drawLine(QPointF(x - 2 * side, cy + 6), QPointF(x + 3 * side, cy - 5))
        p.setPen(QPen(OUTLINE, LINE, Qt.PenStyle.SolidLine, Qt.PenCapStyle.RoundCap))

    def _buttons(self, p: QPainter) -> None:
        p.setBrush(QBrush(self.shade))
        p.setPen(QPen(OUTLINE, 3))
        for y in (-27, -13):
            p.drawEllipse(QPointF(0, y), 4.5, 4.5)
        p.setPen(QPen(OUTLINE, LINE, Qt.PenStyle.SolidLine, Qt.PenCapStyle.RoundCap))

    def _arm(self, p: QPainter, x: float, y: float, raised: float, left: bool) -> None:
        p.save()
        p.translate(x, y)
        p.rotate(raised if left else -raised)
        p.setBrush(QBrush(self.fill))
        p.drawEllipse(QRectF(-11, -6, 22, 20))
        p.restore()

    def _feet(self, p: QPainter, pose: Pose) -> None:
        p.setBrush(QBrush(self.fill))
        p.drawEllipse(QPointF(-22, -4 - pose.foot_l), 14, 9)
        p.drawEllipse(QPointF(22, -4 - pose.foot_r), 14, 9)

    def _ears(self, p: QPainter) -> None:
        p.setBrush(QBrush(self.fill))
        if self.ears == "bumps":
            for x in (-34, 34):
                p.drawEllipse(QPointF(x, -130), 11, 10)
            p.drawEllipse(QPointF(0, -138), 7, 9)
        elif self.ears == "round":
            for x in (-40, 40):
                p.drawEllipse(QPointF(x, -126), 15, 14)
        elif self.ears == "tall":
            for x in (-38, 38):
                p.drawEllipse(QRectF(x - 11, -148, 22, 30))
        else:  # horn
            path = QPainterPath(QPointF(-12, -124))
            path.lineTo(QPointF(0, -160))
            path.lineTo(QPointF(12, -124))
            path.closeSubpath()
            p.drawPath(path)
            for x in (-38, 38):
                p.drawEllipse(QPointF(x, -126), 10, 9)

    def _tail(self, p: QPainter) -> None:
        p.setBrush(QBrush(self.fill))
        path = QPainterPath(QPointF(50, -30))
        path.cubicTo(QPointF(90, -40), QPointF(96, -10), QPointF(74, -6))
        path.cubicTo(QPointF(68, -16), QPointF(60, -20), QPointF(50, -22))
        p.drawPath(path)

    def _sweat(self, p: QPainter) -> None:
        p.setBrush(QBrush(SWEAT))
        p.setPen(QPen(OUTLINE, 3))
        path = QPainterPath(QPointF(58, -128))
        path.cubicTo(QPointF(50, -112), QPointF(50, -104), QPointF(58, -104))
        path.cubicTo(QPointF(66, -104), QPointF(66, -112), QPointF(58, -128))
        p.drawPath(path)


def render_sheet(key: str) -> QImage:
    member = MEMBERS[key]
    image = QImage(SHEET_W, SHEET_H, QImage.Format.Format_ARGB32_Premultiplied)
    image.fill(Qt.GlobalColor.transparent)
    painter = QPainter(image)
    artist = PajamaPainter(member)
    for state, (row, count, _) in STATES.items():
        for i in range(count):
            col, r = i % COLS, row + i // COLS
            painter.save()
            painter.translate(col * CELL_W, r * CELL_H)
            painter.setClipRect(QRectF(0, 0, CELL_W, CELL_H))
            artist.draw(painter, GENERATORS[state](i, count))
            painter.restore()
    painter.end()
    return image


def generate(root: Path, keys: list[str] | None = None) -> list[Path]:
    written = []
    for key in keys or list(MEMBERS):
        folder = root / key
        folder.mkdir(parents=True, exist_ok=True)
        render_sheet(key).save(str(folder / "spritesheet.png"))
        meta = {"id": key, "displayName": MEMBERS[key]["name"], "spriteVersionNumber": 2, "spritesheetPath": "spritesheet.png"}
        (folder / "pet.json").write_text(json.dumps(meta, ensure_ascii=False, indent=2), "utf-8")
        written.append(folder / "spritesheet.png")
    return written

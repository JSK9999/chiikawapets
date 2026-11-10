"""Generate Pajama Partys spritesheets (original fan drawings, Codex v2 layout).

The reference repo has no Pajama Partys, so the four members are drawn here with
QPainter in the same visual style: thick brown outline, pastel fill, big hooded
head. They are faceless: the hood opening is a grey-green rounded square with
small blush strokes in its lower corners.
"""
from __future__ import annotations

import json
import math
from pathlib import Path

from PySide6.QtCore import QPointF, QRectF, Qt
from PySide6.QtGui import QBrush, QColor, QImage, QPainter, QPainterPath, QPen

from .catalog import ALL_STATES, CELL_H, CELL_W, COLS, DANCE_SHEET_H, SHEET_W
from .pajama_poses import GENERATORS, Pose

OUTLINE = QColor("#3b2a24")
FACE = QColor("#7c8e89")
BLUSH = QColor("#3a4744")
SWEAT = QColor("#8fc7f0")
STAR = QColor("#eef2ee")
LINE = 5.0
FIGURE_SCALE = 0.9  # whole figure, so ears and horn stay inside the cell when jumping
HEAD_Y = -114.0  # face centre; pivot for the hip-shake rotation
FACE_W, FACE_H, FACE_R = 124.0, 104.0, 52.0

MEMBERS: dict[str, dict] = {
    "pajama-green": {"name": "파자마 파티즈 (초록)", "fill": "#c6edb9", "shade": "#a9d69a", "ears": "dino", "tail": True},
    "pajama-pink": {"name": "파자마 파티즈 (분홍)", "fill": "#f7c3cf", "shade": "#eba6b6", "ears": "round", "tail": False},
    "pajama-purple": {"name": "파자마 파티즈 (보라)", "fill": "#d2c6e8", "shade": "#b9a9d8", "ears": "tall", "tail": False},
    "pajama-white": {"name": "파자마 파티즈 (흰색)", "fill": "#f6f3ec", "shade": "#e3ddd0", "ears": "horn", "tail": False},
}


def _pen(width: float = LINE) -> QPen:
    return QPen(OUTLINE, width, Qt.PenStyle.SolidLine, Qt.PenCapStyle.RoundCap, Qt.PenJoinStyle.RoundJoin)


class PajamaPainter:
    def __init__(self, member: dict):
        self.fill = QColor(member["fill"])
        self.shade = QColor(member["shade"])
        self.ears = member["ears"]
        self.tail = member["tail"]

    # ----- frame ----------------------------------------------------------
    def draw(self, p: QPainter, pose: Pose) -> None:
        p.save()
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        p.translate(CELL_W / 2 + pose.dx, 198 + pose.dy)  # pivot at the feet
        p.scale(FIGURE_SCALE, FIGURE_SCALE)
        if pose.flip:
            p.scale(-1, 1)
        if pose.pivot_top:
            p.translate(0, HEAD_Y)
            p.rotate(pose.tilt)
            p.translate(0, -HEAD_Y)
        else:
            p.rotate(pose.tilt)
        p.scale(pose.sx, pose.sy)
        p.setPen(_pen())
        if self.tail:
            self._tail(p)
        self._feet(p, pose)
        self._ears(p)
        self._body(p)
        if self._back_view(pose):
            self._back(p, pose)
        else:
            self._face(p, pose)
            self._buttons(p)
        self._arm(p, -58, -52, pose.arm_l, left=True)
        self._arm(p, 58, -52, pose.arm_r, left=False)
        if pose.sweat:
            self._sweat(p)
        p.restore()

    @staticmethod
    def _back_view(pose: Pose) -> bool:
        return bool(pose.peek) or (pose.spin is not None and math.cos(2 * math.pi * pose.spin) <= 0.08)

    # ----- parts ----------------------------------------------------------
    @staticmethod
    def _body_path() -> QPainterPath:
        head = QPainterPath()
        head.addRoundedRect(QRectF(-76, -180, 152, 132), 72, 68)
        lower = QPainterPath()
        lower.addRoundedRect(QRectF(-54, -80, 108, 76), 36, 36)
        return head.united(lower).simplified()

    def _body(self, p: QPainter) -> None:
        p.setBrush(QBrush(self.fill))
        p.drawPath(self._body_path())

    def _face(self, p: QPainter, pose: Pose) -> None:
        fx, fy = pose.face
        squeeze = 1.0
        if pose.spin is not None:  # face slides to the edge and thins while turning
            squeeze = math.cos(2 * math.pi * pose.spin)
            fx += 26 * math.sin(2 * math.pi * pose.spin)
        p.save()
        p.translate(fx, HEAD_Y + fy)
        p.scale(squeeze, 1.0)
        p.setBrush(QBrush(FACE))
        p.drawRoundedRect(QRectF(-FACE_W / 2, -FACE_H / 2, FACE_W, FACE_H), FACE_R, FACE_R)
        if pose.marks == "star":
            self._star(p, QPointF(0, 0))
        else:
            self._marks(p, pose.marks)
        p.restore()

    def _marks(self, p: QPainter, kind: str) -> None:
        p.setPen(QPen(BLUSH, 3.2, Qt.PenStyle.SolidLine, Qt.PenCapStyle.RoundCap))
        for side in (-1, 1):
            cx, cy = side * 40, 30
            if kind == "x":
                p.drawLine(QPointF(cx - 6, cy - 6), QPointF(cx + 6, cy + 6))
                p.drawLine(QPointF(cx - 6, cy + 6), QPointF(cx + 6, cy - 6))
            else:
                for k in (-1, 0, 1):
                    x = cx + k * 6
                    p.drawLine(QPointF(x - 2, cy + 5), QPointF(x + 2, cy - 5))
        p.setPen(_pen())

    def _star(self, p: QPainter, centre: QPointF) -> None:
        """Four-point sparkle the group shows while performing."""
        pts = [(0, -16), (4, -4), (16, 0), (4, 4), (0, 16), (-4, 4), (-16, 0), (-4, -4)]
        path = QPainterPath(QPointF(centre.x() + pts[0][0], centre.y() + pts[0][1]))
        for x, y in pts[1:]:
            path.lineTo(QPointF(centre.x() + x, centre.y() + y))
        path.closeSubpath()
        p.setBrush(QBrush(STAR))
        p.setPen(_pen(2.5))
        p.drawPath(path)
        p.setPen(_pen())

    def _back(self, p: QPainter, pose: Pose) -> None:
        """Seen from behind: a pom on the lower back, face peeking round the hood."""
        p.setBrush(QBrush(STAR))
        p.setPen(_pen(3))
        p.drawEllipse(QPointF(0, -22), 6, 6)
        p.setPen(_pen())
        if pose.peek:
            p.save()
            p.setClipPath(self._body_path())
            centre = QPointF(pose.peek * 58, HEAD_Y + 4)
            p.setBrush(QBrush(FACE))
            p.drawRoundedRect(QRectF(centre.x() - 30, centre.y() - 50, 60, 100), 28, 40)
            if pose.marks == "star":
                p.translate(centre.x() + pose.peek * 6, centre.y())
                p.scale(0.5, 1.0)
                self._star(p, QPointF(0, 0))
            p.restore()

    def _buttons(self, p: QPainter) -> None:
        p.setBrush(QBrush(self.shade))
        p.setPen(_pen(3))
        for y in (-46, -31):
            p.drawEllipse(QPointF(0, y), 4.5, 4.5)
        p.setPen(_pen())

    def _arm(self, p: QPainter, x: float, y: float, raised: float, left: bool) -> None:
        p.save()
        p.translate(x, y)
        p.rotate((-30 if left else 30) + (raised if left else -raised))
        p.setBrush(QBrush(self.fill))
        p.drawRoundedRect(QRectF(-9, -4, 18, 26), 9, 9)
        p.restore()

    def _feet(self, p: QPainter, pose: Pose) -> None:
        p.setBrush(QBrush(self.fill))
        p.drawEllipse(QPointF(-16, -4 - pose.foot_l), 11, 8)
        p.drawEllipse(QPointF(16, -4 - pose.foot_r), 11, 8)

    def _ears(self, p: QPainter) -> None:
        p.setBrush(QBrush(self.fill))
        if self.ears == "dino":
            for x in (-52, 52):
                p.drawEllipse(QPointF(x, -172), 12, 11)
            for x in (-18, 18):
                p.drawEllipse(QPointF(x, -184), 8, 8)
        elif self.ears == "round":
            for x in (-58, 58):
                p.drawEllipse(QPointF(x, -168), 16, 15)
        elif self.ears == "tall":
            for x in (-50, 50):
                p.drawEllipse(QRectF(x - 12, -200, 24, 40))
        else:  # horn
            path = QPainterPath(QPointF(-13, -170))
            path.lineTo(QPointF(0, -198))
            path.lineTo(QPointF(13, -170))
            path.closeSubpath()
            p.drawPath(path)
            for x in (-60, 60):
                p.drawEllipse(QPointF(x, -166), 10, 9)

    def _tail(self, p: QPainter) -> None:
        p.setBrush(QBrush(self.fill))
        path = QPainterPath(QPointF(48, -36))
        path.cubicTo(QPointF(92, -50), QPointF(100, -12), QPointF(78, -10))
        path.cubicTo(QPointF(70, -22), QPointF(62, -26), QPointF(48, -26))
        p.drawPath(path)

    def _sweat(self, p: QPainter) -> None:
        p.setBrush(QBrush(SWEAT))
        p.setPen(_pen(3))
        path = QPainterPath(QPointF(78, -176))
        path.cubicTo(QPointF(70, -160), QPointF(70, -152), QPointF(78, -152))
        path.cubicTo(QPointF(86, -152), QPointF(86, -160), QPointF(78, -176))
        p.drawPath(path)


def render_sheet(key: str) -> QImage:
    member = MEMBERS[key]
    image = QImage(SHEET_W, DANCE_SHEET_H, QImage.Format.Format_ARGB32_Premultiplied)
    image.fill(Qt.GlobalColor.transparent)
    painter = QPainter(image)
    artist = PajamaPainter(member)
    for state, (row, count, _) in ALL_STATES.items():
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

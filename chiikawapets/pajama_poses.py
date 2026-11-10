"""Pose parameters per state and frame for the drawn Pajama Partys."""
from __future__ import annotations

import math
from dataclasses import dataclass


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
    marks: str = "blush"  # blush | x | star
    flip: bool = False
    spin: float | None = None  # 0..1 turn progress; None = facing front
    peek: int = 0  # back turned, face peeking over a shoulder: -1 left, +1 right
    pivot_top: bool = False  # rotate about the head so the hips swing instead


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
        Pose(dy=-12, sx=0.94, sy=1.04, arm_l=60, arm_r=60),
        Pose(dy=-18, arm_l=140, arm_r=140, foot_l=4, foot_r=4),
        Pose(dy=-10, sy=1.03, arm_l=90, arm_r=90),
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


# --- the group's own routine, read off the anime dance clip -------------------
def _dance_point(i: int, n: int) -> Pose:
    """Two bounces per loop; hand on the cheek, swapping hands halfway."""
    bounce = -7 * abs(math.sin(2 * math.pi * i / n * 2))
    right_hand = i < n // 2
    return Pose(
        dy=bounce,
        tilt=-5 if right_hand else 5,
        arm_r=118 if right_hand else 10,
        arm_l=118 if not right_hand else 10,
        foot_l=3 * (i % 2),
        foot_r=3 * ((i + 1) % 2),
        marks="star",
    )


def _dance_up(i: int, n: int) -> Pose:
    t = 2 * math.pi * i / n
    return Pose(dy=-8 * abs(math.sin(t)), tilt=6 * math.sin(t), arm_l=150 + 15 * math.sin(t), arm_r=150 - 15 * math.sin(t), marks="star")


def _dance_spin(i: int, n: int) -> Pose:
    t = i / n
    return Pose(dy=-4 * abs(math.sin(math.pi * t * 2)), arm_l=35, arm_r=35, spin=t, marks="star")


def _dance_shake(i: int, n: int) -> Pose:
    """Back to the audience, looking over the left shoulder, hips swinging."""
    t = 2 * math.pi * i / n
    return Pose(
        tilt=10 * math.sin(t),
        dy=-2 * abs(math.sin(t)),
        arm_r=125,
        arm_l=15,
        foot_l=4 * max(0.0, math.sin(t)),
        foot_r=4 * max(0.0, -math.sin(t)),
        peek=-1,
        pivot_top=True,
        marks="star",
    )


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
    "dance-point": _dance_point,
    "dance-up": _dance_up,
    "dance-spin": _dance_spin,
    "dance-shake": _dance_shake,
}

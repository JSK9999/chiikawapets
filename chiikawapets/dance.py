"""Group choreography: Pajama Partys gather in a line and dance in sync."""
from __future__ import annotations

import random
from typing import TYPE_CHECKING

from PySide6.QtCore import QObject, QTimer

from .catalog import GENERATED
from .motion import Brain, Plan

if TYPE_CHECKING:
    from .manager import PetManager
    from .pet import PetWindow

DANCE_MS = 14_000
GATHER_TIMEOUT_MS = 25_000
AUTO_MIN_S, AUTO_MAX_S = 180, 420
SPACING = 1.15  # of sprite width


def formation_slots(xs: list[float], width: float, left: float, right: float) -> list[float]:
    """Left-edge x for each dancer, centred on the group's mean, inside [left, right]."""
    if not xs:
        return []
    step = width * SPACING
    span = step * (len(xs) - 1)
    start = sum(xs) / len(xs) - span / 2
    start = max(left, min(start, right - span)) if right - span >= left else left
    return [start + i * step for i in range(len(xs))]


class GroupDance(QObject):
    def __init__(self, manager: "PetManager"):
        super().__init__()
        self.manager = manager
        self.phase = "idle"
        self._waiting: set[int] = set()
        self._dancers: list[PetWindow] = []
        self._watchdog = QTimer(self)
        self._watchdog.setSingleShot(True)
        self._watchdog.timeout.connect(self._begin)
        self._auto = QTimer(self)
        self._auto.setSingleShot(True)
        self._auto.timeout.connect(self.start)
        self._schedule_auto()

    def dancers(self) -> list["PetWindow"]:
        return [p for p in self.manager.pets if p.key in GENERATED and not p.paused]

    def start(self) -> bool:
        if self.phase != "idle":
            return False
        group = sorted(self.dancers(), key=lambda p: p.body.x)
        if len(group) < 2:
            self._schedule_auto()
            return False
        bounds = group[0].bounds()
        slots = formation_slots([p.body.x for p in group], group[0].width(), bounds.left, bounds.right)
        self.phase, self._dancers, self._waiting = "gather", group, {id(p) for p in group}
        for pet, slot in zip(group, slots):
            pet.locked = True
            pet.walk_to(slot)
        self._watchdog.start(GATHER_TIMEOUT_MS)
        return True

    def arrived(self, pet: "PetWindow") -> None:
        self._waiting.discard(id(pet))
        if self.phase == "gather" and not self._waiting:
            self._begin()

    def _begin(self) -> None:
        if self.phase != "gather":
            return
        self._watchdog.stop()
        self.phase = "dance"
        live = [p for p in self._dancers if p in self.manager.pets]
        for k, pet in enumerate(sorted(live, key=lambda p: p.body.x)):
            pet.goal_x = None
            pet.start_plan(Plan("running", DANCE_MS))
            pet.anim.sync("running", k % 2)  # neighbours half a beat apart: a wave
        for pet in self.manager.pets:
            if pet not in live and not pet.locked:
                pet.start_plan(Brain.one_shot("waving", 3))
        QTimer.singleShot(DANCE_MS, self._finish)

    def _finish(self) -> None:
        for pet in self._dancers:
            if pet in self.manager.pets:
                pet.locked, pet.goal_x = False, None
                pet.start_plan(Brain.one_shot("waving", 2))
        self._dancers, self.phase = [], "idle"
        self._schedule_auto()

    def _schedule_auto(self) -> None:
        self._auto.start(random.randint(AUTO_MIN_S, AUTO_MAX_S) * 1000)

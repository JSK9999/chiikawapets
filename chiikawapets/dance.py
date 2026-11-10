"""Choreography: pets whose sheet has dance rows gather in a line and dance in sync.

A single dancer simply dances where it stands. The four dance rows hold one loop
in order, so the routine plays them back to back several times.
"""
from __future__ import annotations

import random
from typing import TYPE_CHECKING

from PySide6.QtCore import QObject, QTimer

from .catalog import ALL_STATES, DANCE_STATES
from .motion import Brain, Plan

if TYPE_CHECKING:
    from .manager import PetManager
    from .pet import PetWindow

LOOPS = 5
ROUTINE: tuple[tuple[str, int], ...] = tuple((state, 1) for _ in range(LOOPS) for state in DANCE_STATES)
GATHER_TIMEOUT_MS = 25_000
AUTO_MIN_S, AUTO_MAX_S = 180, 420
SPACING = 1.15  # of sprite width


def step_ms(state: str, loops: int) -> int:
    _, count, frame_ms = ALL_STATES[state]
    return count * frame_ms * loops


def routine_ms(routine=ROUTINE) -> int:
    return sum(step_ms(state, loops) for state, loops in routine)


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
        return [p for p in self.manager.pets if "dance-1" in p.sheet.frames and not p.paused]

    def start(self) -> bool:
        if self.phase != "idle":
            return False
        group = sorted(self.dancers(), key=lambda p: p.body.x)
        if not group:
            self._schedule_auto()
            return False
        bounds = group[0].bounds()
        slots = formation_slots([p.body.x for p in group], group[0].width(), bounds.left, bounds.right)
        self.phase, self._dancers, self._waiting = "gather", group, {id(p) for p in group}
        for pet, slot in zip(group, slots):
            pet.locked = True
            if pet.stationary:
                self._waiting.discard(id(pet))  # dances where it stands
            else:
                pet.walk_to(slot)
        if not self._waiting:
            self._begin()
        else:
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
        for pet in self.manager.pets:
            if pet not in self._dancers and not pet.locked:
                pet.start_plan(Brain.one_shot("waving", 3))
        self._step(0)

    def _step(self, index: int) -> None:
        """Switch every dancer to the next move at the same instant."""
        if self.phase != "dance":
            return
        if index >= len(ROUTINE):
            self._finish()
            return
        state, loops = ROUTINE[index]
        duration = step_ms(state, loops)
        live = sorted((p for p in self._dancers if p in self.manager.pets), key=lambda p: p.body.x)
        for pet in live:
            pet.goal_x = None
            pet.start_plan(Plan(state, duration))
            pet.anim.sync(state, 0)
        QTimer.singleShot(duration, lambda: self._step(index + 1))

    def _finish(self) -> None:
        for pet in self._dancers:
            if pet in self.manager.pets:
                pet.locked, pet.goal_x = False, None
                pet.start_plan(Brain.one_shot("waving", 2))
        self._dancers, self.phase = [], "idle"
        self._schedule_auto()

    def _schedule_auto(self) -> None:
        self._auto.start(random.randint(AUTO_MIN_S, AUTO_MAX_S) * 1000)

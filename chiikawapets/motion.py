"""Pure behaviour and physics, independent of Qt widgets (unit-testable)."""
from __future__ import annotations

import random
from dataclasses import dataclass

from .catalog import STATES

GRAVITY = 2600.0  # px/s^2
WALK_SPEED = 55.0  # px/s at height 128; scaled with size
JUMP_VELOCITY = -520.0
TOSS_FRICTION = 0.985
BOUNCE = 0.25


@dataclass
class Plan:
    state: str
    duration_ms: int
    direction: int = 0  # -1 left, +1 right, 0 still


class Animator:
    """Advances frame index by elapsed time for the active state."""

    def __init__(self) -> None:
        self.state = "idle"
        self.index = 0
        self._elapsed = 0.0

    def set_state(self, state: str) -> None:
        if state != self.state:
            self.state, self.index, self._elapsed = state, 0, 0.0

    def step(self, dt_ms: float) -> None:
        _, count, frame_ms = STATES[self.state]
        if frame_ms <= 0:
            return
        self._elapsed += dt_ms
        while self._elapsed >= frame_ms:
            self._elapsed -= frame_ms
            self.index = (self.index + 1) % count


class Brain:
    """Picks what to do next. Weights favour calm behaviour."""

    ACTIONS = ("idle", "walk", "waiting", "waving", "jumping", "review", "failed")
    WEIGHTS = (30, 34, 12, 8, 8, 5, 3)

    def __init__(self, rng: random.Random | None = None) -> None:
        self.rng = rng or random.Random()

    def next_plan(self, facing: int) -> Plan:
        action = self.rng.choices(self.ACTIONS, self.WEIGHTS)[0]
        if action == "walk":
            direction = facing if self.rng.random() < 0.6 else -facing
            return Plan("running-right" if direction > 0 else "running-left", self.rng.randint(2500, 7000), direction)
        if action in ("jumping", "waving"):
            _, count, frame_ms = STATES[action]
            return Plan(action, count * frame_ms * self.rng.randint(1, 2))
        return Plan(action, self.rng.randint(2000, 6000))

    @staticmethod
    def one_shot(state: str, loops: int = 1) -> Plan:
        _, count, frame_ms = STATES[state]
        return Plan(state, count * frame_ms * loops)


@dataclass
class Bounds:
    left: float
    right: float  # max x for the sprite's left edge
    ground: float  # y of the sprite's top edge when standing


class Body:
    """Position and velocity in screen pixels. y grows downward."""

    def __init__(self, x: float, y: float, height: int) -> None:
        self.x, self.y = x, y
        self.vx, self.vy = 0.0, 0.0
        self.scale = height / 128.0
        self.airborne = False

    def walk(self, direction: int, dt: float, bounds: Bounds) -> int:
        """Move horizontally; returns the direction actually used (flips at edges)."""
        self.x += direction * WALK_SPEED * self.scale * dt
        if self.x < bounds.left:
            self.x, direction = bounds.left, 1
        elif self.x > bounds.right:
            self.x, direction = bounds.right, -1
        return direction

    def jump(self) -> None:
        if not self.airborne:
            self.vy = JUMP_VELOCITY * self.scale
            self.airborne = True

    def toss(self, vx: float, vy: float) -> None:
        self.vx, self.vy, self.airborne = vx, vy, True

    def fall(self, dt: float, bounds: Bounds) -> bool:
        """Apply gravity. Returns True on the frame the body lands."""
        if not self.airborne:
            return False
        self.vy += GRAVITY * self.scale * dt
        self.vx *= TOSS_FRICTION
        self.x = min(max(self.x + self.vx * dt, bounds.left), bounds.right)
        self.y += self.vy * dt
        if self.y >= bounds.ground:
            self.y = bounds.ground
            if self.vy > 260 * self.scale:
                self.vy = -self.vy * BOUNCE
                return False
            self.vx = self.vy = 0.0
            self.airborne = False
            return True
        return False

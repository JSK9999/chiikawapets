"""One transparent always-on-top window per pet."""
from __future__ import annotations

from typing import TYPE_CHECKING

from PySide6.QtCore import QElapsedTimer, QPoint, QPointF, Qt, QTimer
from PySide6.QtGui import QCursor, QGuiApplication, QMouseEvent, QPainter, QPaintEvent
from PySide6.QtWidgets import QWidget

from .motion import Animator, Body, Bounds, Brain, Plan
from .sprites import SpriteSheet, gaze_index

if TYPE_CHECKING:
    from .manager import PetManager

TICK_MS = 16
DRAG_THRESHOLD = 4
LOOK_RADIUS = 420
MAX_TOSS = 1800.0


class PetWindow(QWidget):
    def __init__(self, key: str, sheet: SpriteSheet, manager: "PetManager", x: float, y: float | None = None):
        super().__init__(None)
        self.key, self.sheet, self.manager = key, sheet, manager
        self.setWindowFlags(
            Qt.WindowType.FramelessWindowHint
            | Qt.WindowType.WindowStaysOnTopHint
            | Qt.WindowType.Tool
            | Qt.WindowType.WindowDoesNotAcceptFocus
            | Qt.WindowType.NoDropShadowWindowHint  # cached shadows leave ghost outlines
        )
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground, True)
        self.setAttribute(Qt.WidgetAttribute.WA_MacAlwaysShowToolWindow, True)
        self.setFixedSize(sheet.size)

        self.anim = Animator()
        self.brain = Brain()
        self.body = Body(x, 0.0, sheet.size.height())
        self.body.y = self.bounds().ground if y is None else y
        self.body.airborne = self.body.y < self.bounds().ground - 1
        self.facing = 1
        self.plan = Plan("idle", 1500)
        self.plan_elapsed = 0.0
        self.paused = False
        self.tossed = False
        self.locked = False  # choreography owns this pet; Brain stays quiet
        self.goal_x: float | None = None
        self._press: QPoint | None = None
        self._double = False
        self._dragging = False
        self._offset = QPoint()
        self._last_drag = QPointF()
        self._velocity = QPointF()

        self.move(round(self.body.x), round(self.body.y))
        self._clock = QElapsedTimer()
        self._clock.start()
        self._timer = QTimer(self)
        self._timer.timeout.connect(self._tick)
        self._timer.start(TICK_MS)

    # ----- geometry -------------------------------------------------------
    def bounds(self) -> Bounds:
        centre = self.frameGeometry().center()
        screen = QGuiApplication.screenAt(centre) or QGuiApplication.primaryScreen()
        avail = screen.availableGeometry()
        return Bounds(avail.left(), avail.right() - self.width() + 1, avail.bottom() - self.height() + 1)

    # ----- behaviour ------------------------------------------------------
    def start_plan(self, plan: Plan) -> None:
        self.plan, self.plan_elapsed = plan, 0.0
        if plan.direction:
            self.facing = plan.direction
        if plan.state == "jumping":
            self.body.jump()

    def walk_to(self, x: float) -> None:
        """Walk until the sprite's left edge reaches x, then report arrival."""
        self.goal_x = x
        self.start_plan(Plan("idle", 1))

    def _steer_to_goal(self) -> bool:
        """Returns True when the goal has just been reached."""
        if self.goal_x is None:
            return False
        delta = self.goal_x - self.body.x
        if abs(delta) < 3:
            self.body.x, self.goal_x = self.goal_x, None
            self.start_plan(Plan("idle", 10**9))
            self.manager.dance.arrived(self)
            return True
        want = 1 if delta > 0 else -1
        if self.plan.direction != want:
            self.start_plan(Plan("running-right" if want > 0 else "running-left", 10**9, want))
        return False

    def do(self, state: str) -> None:
        """User-requested action from a menu."""
        self.paused = False
        self.locked, self.goal_x = False, None
        if state.startswith("running"):
            self.start_plan(Plan(state, 5000, 1 if state.endswith("right") else -1))
        elif state in ("idle", "waiting", "review"):
            self.start_plan(Plan(state, 6000))
        else:
            self.start_plan(Brain.one_shot(state, 2))

    def _tick(self) -> None:
        dt_ms = self._clock.restart()
        dt = min(dt_ms, 100) / 1000.0
        if self._dragging or self.paused:
            self.anim.step(dt_ms)
            self.update()
            return
        landed = self.body.fall(dt, self.bounds())
        if self.tossed:
            self.anim.set_state("failed")
            if landed:
                self.tossed = False
                self.start_plan(Brain.one_shot("waiting", 2))
        else:
            self._run_plan(dt, dt_ms)
        self.move(round(self.body.x), round(self.body.y))
        self.anim.step(dt_ms)
        self.update()

    def _run_plan(self, dt: float, dt_ms: float) -> None:
        self.plan_elapsed += dt_ms
        if self._steer_to_goal():
            return
        if self.plan.direction and not self.body.airborne:
            moved = self.body.walk(self.plan.direction, dt, self.bounds())
            if moved != self.plan.direction:
                self.start_plan(Plan("running-right" if moved > 0 else "running-left", self.plan.duration_ms, moved))
        if self.plan_elapsed >= self.plan.duration_ms and not self.body.airborne and not self.locked:
            self.start_plan(self.manager.suggest_plan(self) or self.brain.next_plan(self.facing))
        self.anim.set_state(self._visible_state())

    def _visible_state(self) -> str:
        if self.plan.state != "idle":
            return self.plan.state
        delta = QCursor.pos() - self.frameGeometry().center()
        if abs(delta.x()) > LOOK_RADIUS or abs(delta.y()) > LOOK_RADIUS:
            return "idle"
        self.anim.set_state("look")
        self.anim.index = gaze_index(delta.x(), delta.y())
        return "look"

    # ----- painting -------------------------------------------------------
    def paintEvent(self, event: QPaintEvent) -> None:  # noqa: N802
        painter = QPainter(self)
        painter.setCompositionMode(QPainter.CompositionMode.CompositionMode_Source)
        painter.fillRect(self.rect(), Qt.GlobalColor.transparent)
        painter.setCompositionMode(QPainter.CompositionMode.CompositionMode_SourceOver)
        painter.setRenderHint(QPainter.RenderHint.SmoothPixmapTransform)
        painter.drawPixmap(0, 0, self.sheet.frame(self.anim.state, self.anim.index))

    # ----- input ----------------------------------------------------------
    def mousePressEvent(self, event: QMouseEvent) -> None:  # noqa: N802
        if event.button() != Qt.MouseButton.LeftButton:
            return super().mousePressEvent(event)
        if not self.sheet.hit(self.anim.state, self.anim.index, event.position().toPoint()):
            event.ignore()
            return
        self._begin_press(event)
        event.accept()

    def _begin_press(self, event: QMouseEvent) -> None:
        self._press = event.globalPosition().toPoint()
        self._offset = self._press - self.pos()
        self._last_drag = event.globalPosition()
        self._velocity = QPointF()
        self._double = False

    def mouseMoveEvent(self, event: QMouseEvent) -> None:  # noqa: N802
        if self._press is None:
            return
        here = event.globalPosition()
        if not self._dragging and (here.toPoint() - self._press).manhattanLength() > DRAG_THRESHOLD:
            self._dragging, self.tossed = True, False
            self.anim.set_state("failed")
        if self._dragging:
            self._velocity = (here - self._last_drag) * 0.5 + self._velocity * 0.5
            self._last_drag = here
            target = here.toPoint() - self._offset
            self.body.x, self.body.y = float(target.x()), float(target.y())
            self.move(target)

    def mouseReleaseEvent(self, event: QMouseEvent) -> None:  # noqa: N802
        if event.button() != Qt.MouseButton.LeftButton or self._press is None:
            return
        was_drag, self._dragging, self._press = self._dragging, False, None
        if was_drag:
            vx = max(-MAX_TOSS, min(MAX_TOSS, self._velocity.x() * 60.0))
            vy = max(-MAX_TOSS, min(MAX_TOSS, self._velocity.y() * 60.0))
            self.body.toss(vx, vy)
            self.tossed = True
            self.start_plan(Plan("failed", 10_000))
        elif not self._double:
            self.do("waving")

    def mouseDoubleClickEvent(self, event: QMouseEvent) -> None:  # noqa: N802
        """Second press of a double click: jump, but keep drag possible."""
        if event.button() == Qt.MouseButton.LeftButton:
            self._begin_press(event)
            self._double = True
            self.do("jumping")

    def contextMenuEvent(self, event) -> None:  # noqa: N802
        self.manager.show_pet_menu(self, event.globalPos())

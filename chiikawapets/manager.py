"""Owns the pets, the menu bar icon, and shared settings."""
from __future__ import annotations

import random
import time
from pathlib import Path

from PySide6.QtCore import QPoint
from PySide6.QtGui import QAction, QGuiApplication, QIcon
from PySide6.QtWidgets import QApplication, QMenu, QSystemTrayIcon

from . import macos
from .catalog import CHARACTERS, SIZE_PRESETS
from .config import Config
from .dance import GroupDance
from .motion import Brain, Plan
from .paths import sheet_path
from .pet import PetWindow
from .sprites import SpriteSheet

GREET_COOLDOWN_S = 25.0


class PetManager:
    def __init__(self, app: QApplication, config: Config, assets: Path):
        self.app, self.config, self.assets = app, config, assets
        self.pets: list[PetWindow] = []
        self._sheets: dict[tuple[str, int, float], SpriteSheet] = {}
        self._last_greet: dict[int, float] = {}
        self.dance = GroupDance(self)
        self.tray = self._build_tray()

    # ----- assets ---------------------------------------------------------
    def available(self, key: str) -> bool:
        return sheet_path(key, self.assets).is_file()

    def sheet(self, key: str) -> SpriteSheet:
        dpr = QGuiApplication.primaryScreen().devicePixelRatio()
        cache_key = (key, self.config.height, dpr)
        if cache_key not in self._sheets:
            self._sheets[cache_key] = SpriteSheet(sheet_path(key, self.assets), self.config.height, dpr)
        return self._sheets[cache_key]

    # ----- pets -----------------------------------------------------------
    def spawn(self, key: str, x: float | None = None, y: float | None = None, persist: bool = True) -> PetWindow | None:
        if not self.available(key):
            return None
        sheet = self.sheet(key)
        avail = QGuiApplication.primaryScreen().availableGeometry()
        max_x = max(avail.left(), avail.right() - sheet.size.width() + 1)
        if x is None:
            x = random.uniform(avail.left(), max_x)
        # A window first shown off-screen never paints on macOS, so clamp.
        x = min(max(x, float(avail.left())), float(max_x))
        pet = PetWindow(key, sheet, self, x, y)
        pet.show()
        macos.disable_shadow(int(pet.winId()))
        macos.show_on_all_spaces(int(pet.winId()), self.config.all_spaces)
        self.pets.append(pet)
        if persist:
            self.config.pets = [p.key for p in self.pets]
            self.config.save()
        return pet

    def remove(self, pet: PetWindow) -> None:
        if pet in self.pets:
            self.pets.remove(pet)
        self.dance.arrived(pet)
        pet.close()
        pet.deleteLater()
        self.config.pets = [p.key for p in self.pets]
        self.config.save()

    def set_height(self, height: int) -> None:
        self.config.height = height
        self.config.save()
        old = [(p.key, p.body.x) for p in self.pets]
        for pet in list(self.pets):
            self.remove(pet)
        for key, x in old:
            self.spawn(key, x, persist=False)
        self.config.pets = [p.key for p in self.pets]
        self.config.save()

    def set_all_spaces(self, enabled: bool) -> None:
        self.config.all_spaces = enabled
        self.config.save()
        for pet in self.pets:
            macos.show_on_all_spaces(int(pet.winId()), enabled)

    def everyone(self, state: str) -> None:
        for pet in self.pets:
            pet.do(state)

    def suggest_plan(self, pet: PetWindow) -> Plan | None:
        """Occasionally make two nearby pets greet each other."""
        now = time.monotonic()
        if pet.locked or now - self._last_greet.get(id(pet), 0.0) < GREET_COOLDOWN_S or random.random() > 0.5:
            return None
        for other in self.pets:
            if other is pet or other.body.airborne or other.paused or other.locked:
                continue
            if abs(other.body.x - pet.body.x) < pet.width() * 1.3 and abs(other.body.y - pet.body.y) < pet.height():
                self._last_greet[id(pet)] = self._last_greet[id(other)] = now
                other.start_plan(Brain.one_shot("waving", 2))
                return Brain.one_shot("waving", 2)
        return None

    # ----- menus ----------------------------------------------------------
    def _add_character_menu(self, parent: QMenu) -> None:
        sub = parent.addMenu("캐릭터 추가")
        for key, label in CHARACTERS.items():
            action = sub.addAction(label)
            action.setEnabled(self.available(key))
            action.triggered.connect(lambda _=False, k=key: self.spawn(k))

    def _size_menu(self, parent: QMenu) -> None:
        sub = parent.addMenu("크기")
        for label, height in SIZE_PRESETS.items():
            action = sub.addAction(f"{label} ({height}px)")
            action.setCheckable(True)
            action.setChecked(height == self.config.height)
            action.triggered.connect(lambda _=False, h=height: self.set_height(h))

    def _common_menu(self, menu: QMenu) -> None:
        self._add_character_menu(menu)
        self._size_menu(menu)
        spaces = menu.addAction("모든 데스크톱(Space)에 표시")
        spaces.setCheckable(True)
        spaces.setChecked(self.config.all_spaces)
        spaces.toggled.connect(self.set_all_spaces)
        if self.dance.dancers():
            menu.addAction("춤추기").triggered.connect(self.dance.start)
        menu.addSeparator()
        menu.addAction("모두 인사").triggered.connect(lambda: self.everyone("waving"))
        menu.addAction("모두 점프").triggered.connect(lambda: self.everyone("jumping"))
        menu.addSeparator()
        menu.addAction("종료").triggered.connect(self.app.quit)

    def show_pet_menu(self, pet: PetWindow, at: QPoint) -> None:
        menu = QMenu()
        title = menu.addAction(CHARACTERS[pet.key])
        title.setEnabled(False)
        menu.addSeparator()
        actions = [("인사하기", "waving"), ("점프", "jumping"), ("쉬기", "waiting"), ("왼쪽으로 걷기", "running-left"), ("오른쪽으로 걷기", "running-right")]
        for label, state in actions:
            menu.addAction(label).triggered.connect(lambda _=False, s=state: pet.do(s))
        pause = menu.addAction("다시 움직이기" if pet.paused else "잠깐 멈추기")
        pause.triggered.connect(lambda: setattr(pet, "paused", not pet.paused))
        menu.addAction("이 캐릭터 숨기기").triggered.connect(lambda: self.remove(pet))
        menu.addSeparator()
        self._common_menu(menu)
        menu.exec(at)

    def _build_tray(self) -> QSystemTrayIcon | None:
        if not QSystemTrayIcon.isSystemTrayAvailable():
            return None
        icon_key = next((k for k in ("chiikawa", *CHARACTERS) if self.available(k)), None)
        tray = QSystemTrayIcon(self.app)
        if icon_key:
            pixmap = SpriteSheet(sheet_path(icon_key, self.assets), 36).frame("idle", 0)
            tray.setIcon(QIcon(pixmap))
        tray.setToolTip("Chiikawa Pets")
        menu = QMenu()
        self._common_menu(menu)
        tray.setContextMenu(menu)
        tray.show()
        self._tray_menu = menu  # keep alive
        return tray

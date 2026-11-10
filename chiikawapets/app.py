"""Application entry point."""
from __future__ import annotations

import sys

from PySide6.QtWidgets import QApplication, QMessageBox, QProgressDialog

from . import macos
from .catalog import GENERATED, REPO_URL
from .config import Config
from .download import download, missing
from .manager import PetManager
from .pajama import generate
from .paths import assets_dir


def ensure_generated(root) -> None:
    """Pajama Partys are drawn on this machine; (re)generate when absent."""
    absent = [k for k in GENERATED if not (root / k / "spritesheet.png").is_file()]
    if absent:
        generate(root, absent)


def ensure_assets(config: Config) -> bool:
    root = assets_dir()
    ensure_generated(root)
    if not missing(root, config.pets):
        return True
    answer = QMessageBox.question(
        None,
        "캐릭터 이미지 받기",
        "캐릭터 스프라이트가 아직 없습니다.\n\n"
        f"원본 팬 프로젝트({REPO_URL})에서 개인용으로 내려받을까요?\n"
        "비상업·재배포 금지 조건을 지켜 주세요.\n\n"
        f"저장 위치: {root}",
    )
    if answer != QMessageBox.StandardButton.Yes:
        return False
    dialog = QProgressDialog("다운로드 중...", None, 0, 1)
    dialog.setMinimumDuration(0)
    dialog.show()

    def progress(label: str, done: int, total: int) -> None:
        dialog.setMaximum(total)
        dialog.setValue(done)
        dialog.setLabelText(label)
        QApplication.processEvents()

    errors = download(root, progress=progress)
    dialog.close()
    if errors:
        QMessageBox.warning(None, "일부 다운로드 실패", "\n".join(errors[:10]))
    return not missing(root, config.pets)


def main() -> int:
    app = QApplication(sys.argv)
    app.setApplicationName("ChiikawaPets")
    app.setQuitOnLastWindowClosed(False)
    macos.hide_dock_icon()
    config = Config.load()
    if not ensure_assets(config):
        return 1
    manager = PetManager(app, config, assets_dir())
    for key in config.pets:
        manager.spawn(key, persist=False)
    if not manager.pets:
        QMessageBox.critical(None, "Chiikawa Pets", "표시할 캐릭터가 없습니다. 에셋을 확인해 주세요.")
        return 1
    return app.exec()

"""Application entry point."""
from __future__ import annotations

import sys

from PySide6.QtWidgets import QApplication, QMessageBox, QProgressDialog

from . import macos
from .catalog import REPO_URL
from .config import Config
from .download import download, missing
from .manager import PetManager
from .paths import assets_dir


def ensure_assets(config: Config) -> bool:
    """Fetch missing character assets for personal use, showing progress. No prompt:
    start.command normally does this in the terminal first, so this is a fallback."""
    root = assets_dir()
    if not missing(root, config.pets):
        return True
    print(f"캐릭터 이미지를 개인용으로 내려받습니다 (원본: {REPO_URL}) -> {root}")
    dialog = QProgressDialog("캐릭터 이미지 다운로드 중...", None, 0, 1)
    dialog.setWindowTitle("Chiikawa Pets")
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

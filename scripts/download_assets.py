#!/usr/bin/env python3
"""CLI wrapper: python scripts/download_assets.py"""
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
from PySide6.QtGui import QGuiApplication  # noqa: E402

from chiikawapets.download import main  # noqa: E402

_app = QGuiApplication([])  # GIF-built sheets need a Qt application for painting
raise SystemExit(main())

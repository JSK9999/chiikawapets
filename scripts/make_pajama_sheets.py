#!/usr/bin/env python3
"""Regenerate the Pajama Partys spritesheets: python scripts/make_pajama_sheets.py"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from PySide6.QtGui import QGuiApplication  # noqa: E402

from chiikawapets.pajama import generate  # noqa: E402
from chiikawapets.paths import assets_dir  # noqa: E402

app = QGuiApplication([])
for path in generate(assets_dir()):
    print("wrote", path)

# -*- mode: python ; coding: utf-8 -*-
# Build: .venv/bin/pyinstaller ChiikawaPets.spec
# Assets are intentionally NOT bundled (reference project forbids redistribution);
# the app downloads them to ~/Library/Application Support/ChiikawaPets on first run.
from PyInstaller.utils.hooks import collect_submodules

a = Analysis(
    ["main.py"],
    pathex=["."],
    binaries=[],
    datas=[],
    hiddenimports=collect_submodules("chiikawapets"),
    excludes=["PySide6.QtWebEngineCore", "PySide6.QtWebEngineWidgets", "PySide6.QtQml", "PySide6.QtQuick", "PySide6.Qt3DCore", "PySide6.QtMultimedia", "PySide6.QtCharts", "PySide6.QtPdf"],
    noarchive=False,
)
pyz = PYZ(a.pure)
exe = EXE(
    pyz,
    a.scripts,
    exclude_binaries=True,
    name="ChiikawaPets",
    console=False,
    target_arch=None,
)
coll = COLLECT(exe, a.binaries, a.datas, name="ChiikawaPets")
app = BUNDLE(
    coll,
    name="ChiikawaPets.app",
    icon=None,
    bundle_identifier="dev.local.chiikawapets",
    info_plist={
        "LSUIElement": True,  # menu bar only, no Dock icon
        "NSHighResolutionCapable": True,
        "CFBundleShortVersionString": "1.0.0",
        "CFBundleDisplayName": "Chiikawa Pets",
    },
)

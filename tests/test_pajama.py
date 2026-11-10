import os

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
from PySide6.QtGui import QGuiApplication  # noqa: E402

from chiikawapets.catalog import CELL_H, CELL_W, COLS, GENERATED, SHEET_H, SHEET_W, STATES  # noqa: E402
from chiikawapets.download import downloadable, missing  # noqa: E402
from chiikawapets.pajama import MEMBERS, generate, render_sheet  # noqa: E402

_app = QGuiApplication.instance() or QGuiApplication([])


def _opaque(image, x0, y0):
    return any(image.pixelColor(x, y).alpha() > 0 for y in range(y0, y0 + CELL_H, 8) for x in range(x0, x0 + CELL_W, 8))


def test_members_match_catalog():
    assert set(MEMBERS) == GENERATED


def test_sheet_has_every_frame_and_nothing_else():
    image = render_sheet("pajama-green")
    assert (image.width(), image.height()) == (SHEET_W, SHEET_H)
    used = set()
    for row, count, _ in STATES.values():
        for i in range(count):
            col, r = i % COLS, row + i // COLS
            used.add((col, r))
            assert _opaque(image, col * CELL_W, r * CELL_H)
    for r in range(SHEET_H // CELL_H):
        for col in range(COLS):
            if (col, r) not in used:
                assert not _opaque(image, col * CELL_W, r * CELL_H)


def test_generate_writes_files(tmp_path):
    written = generate(tmp_path, ["pajama-pink"])
    assert written == [tmp_path / "pajama-pink" / "spritesheet.png"]
    assert (tmp_path / "pajama-pink" / "pet.json").is_file()


def test_generated_keys_are_not_downloaded(tmp_path):
    assert not set(downloadable()) & GENERATED
    assert missing(tmp_path, ["pajama-green"]) == []

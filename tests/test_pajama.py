import os

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
from PySide6.QtGui import QGuiApplication  # noqa: E402

from chiikawapets.catalog import ALL_STATES, CELL_H, CELL_W, COLS, DANCE_SHEET_H, GENERATED, SHEET_W  # noqa: E402
from chiikawapets.download import downloadable, missing  # noqa: E402
from chiikawapets.pajama import MEMBERS, generate, render_sheet  # noqa: E402
from chiikawapets.sprites import SpriteSheet  # noqa: E402

_app = QGuiApplication.instance() or QGuiApplication([])


def _opaque(image, x0, y0):
    return any(image.pixelColor(x, y).alpha() > 0 for y in range(y0, y0 + CELL_H, 8) for x in range(x0, x0 + CELL_W, 8))


def test_members_match_catalog():
    assert set(MEMBERS) == GENERATED


def test_sheet_has_every_frame_and_nothing_else():
    image = render_sheet("pajama-green")
    assert (image.width(), image.height()) == (SHEET_W, DANCE_SHEET_H)
    used = set()
    for row, count, _ in ALL_STATES.values():
        for i in range(count):
            col, r = i % COLS, row + i // COLS
            used.add((col, r))
            assert _opaque(image, col * CELL_W, r * CELL_H)
    for r in range(DANCE_SHEET_H // CELL_H):
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


def test_tall_sheet_loads_dance_frames_and_short_sheet_falls_back(tmp_path):
    generate(tmp_path, ["pajama-white"])
    tall = SpriteSheet(tmp_path / "pajama-white" / "spritesheet.png", 64)
    assert tall.frame_count("dance-spin") == 8
    short = render_sheet("pajama-white").copy(0, 0, SHEET_W, CELL_H * 11)
    short.save(str(tmp_path / "short.png"))
    base = SpriteSheet(tmp_path / "short.png", 64)
    assert "dance-spin" not in base.frames
    assert base.frame("dance-spin", 0) is base.frame("idle", 0)

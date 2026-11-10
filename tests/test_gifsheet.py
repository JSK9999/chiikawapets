import os

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
from PySide6.QtCore import QPointF, Qt  # noqa: E402
from PySide6.QtGui import QBrush, QColor, QGuiApplication, QImage, QPainter, QPen, qAlpha  # noqa: E402

from chiikawapets.catalog import ALL_STATES, CELL_H, CELL_W, DANCE_SHEET_H, SHEET_W  # noqa: E402
from chiikawapets.gifcut import bounding_box, cut_character  # noqa: E402
from chiikawapets.gifsheet import resample_indices, state_frames, widest  # noqa: E402
from chiikawapets.sprites import SpriteSheet  # noqa: E402

_app = QGuiApplication.instance() or QGuiApplication([])


def _scene() -> QImage:
    """Blue sky, a yellow outlined blob in the middle, a pink outlined note top-left."""
    img = QImage(200, 160, QImage.Format.Format_ARGB32)
    img.fill(QColor("#a9daee"))
    p = QPainter(img)
    p.setRenderHint(QPainter.RenderHint.Antialiasing)
    p.setPen(QPen(QColor("#3a2a24"), 4))
    p.setBrush(QBrush(QColor("#f5d87a")))
    p.drawEllipse(QPointF(100, 90), 40, 50)
    p.setBrush(QBrush(QColor("#fbf1d9")))
    p.drawEllipse(QPointF(100, 75), 24, 20)  # "face" enclosed by outline
    p.setBrush(QBrush(QColor("#f28bb5")))
    p.drawEllipse(QPointF(30, 30), 10, 10)  # distractor
    p.end()
    return img


def test_cut_keeps_character_and_face_but_not_background_or_distractor():
    cut = cut_character(_scene(), hues=((35, 70),))
    assert qAlpha(cut.pixel(100, 120)) == 255  # yellow body
    assert qAlpha(cut.pixel(100, 75)) == 255  # enclosed face
    assert qAlpha(cut.pixel(5, 150)) == 0  # sky
    assert qAlpha(cut.pixel(30, 30)) == 0  # note
    x0, y0, x1, y1 = bounding_box([cut])
    assert 50 <= x0 <= 60 and 140 <= x1 <= 150 and 30 <= y0 <= 42 and 138 <= y1 <= 146


def test_resample_is_even_in_time():
    assert resample_indices([100, 100, 100, 100], 4) == [0, 1, 2, 3]
    assert resample_indices([300, 100], 4) == [0, 0, 0, 1]
    assert resample_indices([50] * 79, 32)[-1] == 76


def test_widest_prefers_wide_frames_in_time_order():
    frames = []
    for width in (20, 60, 20, 80, 20):
        im = QImage(100, 50, QImage.Format.Format_ARGB32)
        im.fill(0)
        p = QPainter(im)
        p.fillRect(50 - width // 2, 10, width, 30, Qt.GlobalColor.black)
        p.end()
        frames.append(im)
    assert widest(frames, 2) == [1, 3]


def test_state_frames_cover_every_state():
    blank = [QImage(10, 10, QImage.Format.Format_ARGB32) for _ in range(32)]
    frames = state_frames(blank)
    for state, (_, count, _) in ALL_STATES.items():
        assert len(frames[state]) == count, state


def test_build_sheet_from_synthetic_gif(tmp_path):
    from chiikawapets.gifsheet import build_sheet

    gif = tmp_path / "src.gif"
    scene = _scene().convertToFormat(QImage.Format.Format_Indexed8)
    assert scene.save(str(gif), "GIF") or _scene().save(str(gif), "PNG")
    out = build_sheet(gif if gif.is_file() else gif, tmp_path / "spritesheet.png", hues=((35, 70),))
    sheet = SpriteSheet(out, 64)
    assert sheet.frame_count("dance-1") == 8
    assert QImage(str(out)).size().toTuple() == (SHEET_W, DANCE_SHEET_H)

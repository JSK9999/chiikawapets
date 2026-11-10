from chiikawapets.catalog import DANCE_STATES
from chiikawapets.dance import ROUTINE, SPACING, formation_slots, routine_ms, step_ms
from chiikawapets.motion import Animator


def test_slots_centred_and_spaced():
    slots = formation_slots([100.0, 500.0, 300.0], 100.0, 0.0, 2000.0)
    assert len(slots) == 3
    assert abs(slots[1] - slots[0] - 100.0 * SPACING) < 1e-6
    assert abs(slots[2] - slots[1] - 100.0 * SPACING) < 1e-6
    assert abs((slots[0] + slots[2]) / 2 - 300.0) < 1e-6


def test_slots_clamped_to_screen():
    slots = formation_slots([5.0, 10.0, 15.0, 20.0], 100.0, 0.0, 1000.0)
    assert slots[0] == 0.0
    slots = formation_slots([990.0, 995.0], 100.0, 0.0, 1000.0)
    assert slots[-1] == 1000.0


def test_slots_degenerate_cases():
    assert formation_slots([], 100.0, 0.0, 500.0) == []
    assert formation_slots([50.0, 60.0, 70.0], 100.0, 0.0, 150.0)[0] == 0.0


def test_animator_sync_resets_timing():
    anim = Animator()
    anim.set_state("running")
    anim.step(100)
    anim.sync("running", 1)
    assert anim.index == 1
    anim.step(119)
    assert anim.index == 1


def test_routine_plays_the_loop_in_order_about_fifteen_seconds():
    assert all(state in DANCE_STATES for state, _ in ROUTINE)
    assert [s for s, _ in ROUTINE[:4]] == list(DANCE_STATES)
    assert step_ms("dance-3", 1) == 8 * 90
    assert 10_000 <= routine_ms() <= 20_000

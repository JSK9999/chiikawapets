import random

from chiikawapets.catalog import STATES
from chiikawapets.motion import Animator, Body, Bounds, Brain, Plan
from chiikawapets.sprites import gaze_index


def test_animator_advances_and_wraps():
    anim = Animator()
    anim.set_state("waving")  # 4 frames x 140ms
    anim.step(140 * 4 + 10)
    assert anim.index == 0
    anim.step(140)
    assert anim.index == 1


def test_animator_static_state_keeps_index():
    anim = Animator()
    anim.set_state("look")
    anim.index = 7
    anim.step(5000)
    assert anim.index == 7


def test_brain_plans_are_valid_states():
    brain = Brain(random.Random(1))
    for _ in range(200):
        plan = brain.next_plan(1)
        assert plan.state in STATES
        assert plan.duration_ms > 0
        if plan.direction:
            assert plan.state.startswith("running-")


def test_walk_flips_at_edges():
    body = Body(x=0.0, y=0.0, height=128)
    bounds = Bounds(left=0, right=100, ground=0)
    assert body.walk(-1, 1.0, bounds) == 1
    assert body.x == 0
    body.x = 100
    assert body.walk(1, 1.0, bounds) == -1


def test_fall_lands_and_stops():
    body = Body(x=10.0, y=0.0, height=128)
    body.toss(0.0, 0.0)
    bounds = Bounds(left=0, right=500, ground=300)
    landed = False
    for _ in range(600):
        if body.fall(1 / 60, bounds):
            landed = True
            break
    assert landed and body.y == 300 and not body.airborne


def test_gaze_index_quadrants():
    assert gaze_index(0, -10) == 0  # up
    assert gaze_index(10, 0) == 4  # right
    assert gaze_index(0, 10) == 8  # down
    assert gaze_index(-10, 0) == 12  # left


def test_one_shot_duration():
    plan = Brain.one_shot("jumping", 2)
    assert plan == Plan("jumping", 5 * 140 * 2)

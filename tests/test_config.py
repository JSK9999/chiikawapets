from chiikawapets.config import Config


def test_defaults_when_garbage():
    cfg = Config.from_dict({"pets": ["nope", 3], "height": "big", "all_spaces": "yes"})
    assert cfg.pets == ["chiikawa", "hachiware", "usagi"]
    assert cfg.height == 128
    assert cfg.all_spaces is True


def test_valid_values_kept():
    cfg = Config.from_dict({"pets": ["usagi", "momonga"], "height": 160, "all_spaces": False})
    assert cfg.pets == ["usagi", "momonga"]
    assert cfg.height == 160
    assert cfg.all_spaces is False


def test_height_out_of_range_ignored():
    assert Config.from_dict({"height": 10}).height == 128
    assert Config.from_dict({"height": 9999}).height == 128

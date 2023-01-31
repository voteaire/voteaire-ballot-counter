import sys

from unit.api.fixtures import api


def test_simple(monkeypatch):
    sys.path.append("src")

    from meta.vote_weighter import SimpleVoteWeighter
    from meta.chain_providers import mock

    weighter = SimpleVoteWeighter()

    assert weighter.vote_type() == "Simple"

    assert weighter.weight_vote("stake123", 192, {"Name": "Simple"}, mock) == {
        "status": "success",
        "vote_weight": 4882704265,
    }

    assert weighter.weight_vote("stake123", 198, {"Name": "Simple"}, mock) == {
        "status": "future-epoch",
    }

    monkeypatch.setattr(
        "meta.chain_providers.mock.get_epoch_snapshot", lambda x, y: None
    )

    assert weighter.weight_vote("stake123", 192, {"Name": "Simple"}, mock) == {
        "status": "invalid",
        "message": "User did not have registered delegation before the snapshot! Epoch snapshot not found!",
    }

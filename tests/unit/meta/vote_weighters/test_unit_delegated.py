import sys

from unit.api.fixtures import api


def test_simple(monkeypatch):
    sys.path.append("src")

    from meta.vote_weighter import DelegatedVoteWeighter
    from meta.chain_providers import mock

    weighter = DelegatedVoteWeighter()

    assert weighter.vote_type() == "Delegated"

    assert weighter.weight_vote(
        "stake123", 192, {"Name": "Delegated", "PoolId": "pool123"}, mock
    ) == {"status": "success", "vote_weight": 4882704265}

    assert weighter.weight_vote(
        "stake123", 198, {"Name": "Delegated", "PoolId": "pool123"}, mock
    ) == {
        "status": "future-epoch",
    }

    assert weighter.weight_vote(
        "stake123", 192, {"Name": "Delegated", "PoolId": "pool456"}, mock
    ) == {
        "status": "invalid",
        "message": "User did not delegate to right pool. Expected pool456 but got pool123",
    }

    monkeypatch.setattr(
        "meta.chain_providers.mock.get_epoch_snapshot", lambda x, y: None
    )

    assert weighter.weight_vote(
        "stake123", 192, {"Name": "Delegated", "PoolId": "pool123"}, mock
    ) == {
        "status": "invalid",
        "message": "User did not have registered delegation before the snapshot! Epoch snapshot not found!",
    }

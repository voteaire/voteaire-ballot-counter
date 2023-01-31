import sys

from unit.api.fixtures import api


def test_policy_id(monkeypatch):
    sys.path.append("src")

    from meta.vote_weighter import PolicyIdVoteWeighter
    from lib.mock import snapshotter_utils

    weighter = PolicyIdVoteWeighter()

    assert weighter.vote_type() == "PolicyId"

    monkeypatch.setattr(
        "meta.vote_weighter.policy_id.snapshotter_utils.register_snapshot",
        snapshotter_utils.register_snapshot,
    )

    assert weighter.weight_vote(
        "stake123", 198, {"Name": "PolicyId", "PolicyId": "abc123"}
    ) == {
        "status": "future-epoch",
    }

    monkeypatch.setattr(
        "meta.vote_weighter.policy_id.snapshotter_utils.register_snapshot",
        snapshotter_utils.helper_get_processed_snapshot,
    )

    assert weighter.weight_vote(
        "stake123", 198, {"Name": "PolicyId", "PolicyId": "abc123"}
    ) == {
        "status": "future-epoch",
    }

    monkeypatch.setattr(
        "meta.vote_weighter.policy_id.snapshotter_utils.register_snapshot",
        snapshotter_utils.helper_get_failing_snapshot,
    )

    assert weighter.weight_vote(
        "stake123", 198, {"Name": "PolicyId", "PolicyId": "abc123"}
    ) == {"status": "invalid", "message": "Error Creating Snapshot"}

    monkeypatch.setattr(
        "meta.vote_weighter.policy_id.snapshotter_utils.register_snapshot",
        snapshotter_utils.helper_get_completed_snapshot,
    )

    monkeypatch.setattr(
        "meta.vote_weighter.policy_id.snapshotter_utils.get_assets",
        snapshotter_utils.get_assets,
    )

    assert weighter.weight_vote(
        "stake123", 192, {"Name": "PolicyId", "PolicyId": "abc123"}
    ) == {"status": "success", "vote_weight": 1_000}

    monkeypatch.setattr(
        "meta.vote_weighter.policy_id.snapshotter_utils.get_assets",
        snapshotter_utils.helper_get_failing_assets,
    )

    assert weighter.weight_vote(
        "stake123", 192, {"Name": "PolicyId", "PolicyId": "abc123"}
    ) == {"status": "error", "message": "an error occured"}

    monkeypatch.setattr(
        "meta.vote_weighter.policy_id.snapshotter_utils.get_assets",
        snapshotter_utils.helper_get_no_snapshot_assets,
    )

    assert weighter.weight_vote(
        "stake123", 192, {"Name": "PolicyId", "PolicyId": "abc123"}
    ) == {
        "status": "error",
        "message": 'Incosistent snapshotter. Received "completed" status but got "no_snapshot" return value!',
    }

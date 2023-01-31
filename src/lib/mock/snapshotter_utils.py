def register_snapshot(policy_id: str, epoch_number: int) -> dict:
    return {
        "status": "queued",
        "snapshot_id": "52f41186-8f35-4557-ab23-077b1eef1d9b",
    }


def helper_get_failing_snapshot(policy_id: str, epoch_number: int) -> dict:
    return {"status": "failed", "message": "Error Creating Snapshot"}


def helper_get_processed_snapshot(policy_id: str, epoch_number: int) -> dict:
    return {
        "status": "processed",
        "snapshot_id": "52f41186-8f35-4557-ab23-077b1eef1d9b",
    }


def helper_get_completed_snapshot(policy_id: str, epoch_number: int) -> dict:
    return {
        "status": "complete",
        "snapshot_id": "52f41186-8f35-4557-ab23-077b1eef1d9b",
    }


def get_snapshot_state(policy_id: str, epoch_number: int) -> dict:
    return {"status": "queued", "snapshot_id": "52f41186-8f35-4557-ab23-077b1eef1d9b"}


def get_assets(policy_id: str, epoch_number: int, stake_address: str = None) -> dict:
    result = {
        "status": "success",
        "assets": [
            {"asset_name": "asset_name1", "amount": 400},
            {"asset_name": "asset_name2", "amount": 600},
        ],
    }

    return result


def helper_get_no_snapshot_assets(
    policy_id: str, epoch_number: int, stake_address: str = None
) -> dict:
    return {"status": "no_snapshot"}


def helper_get_failing_assets(
    policy_id: str, epoch_number: int, stake_address: str = None
) -> dict:
    return {"status": "error", "message": "an error occured"}

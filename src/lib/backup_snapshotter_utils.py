import logging
import requests
import dotenv
import os


dotenv.load_dotenv()

SNAPSHOTTER_ENDPOINT = os.getenv("SNAPSHOTTER_ENDPOINT")
if SNAPSHOTTER_ENDPOINT is None:
    raise ValueError("Snapshotter endpoint undefined!")


def register_snapshot(policy_id: str, epoch_number: int) -> dict:
    logging.info("Next process >>>>>")
    r = requests.post(
        f"{SNAPSHOTTER_ENDPOINT}/policy_snapshot/{policy_id}/{epoch_number}", timeout=5
    )

    if r.status_code != 200:
        logging.warning(r.json())
        raise requests.RequestException(f"Received status code {r.status_code}!")

    return r.json()


def get_snapshot_state(policy_id: str, epoch_number: int) -> dict:
    r = requests.get(
        f"{SNAPSHOTTER_ENDPOINT}/policy_snapshot/{policy_id}/{epoch_number}"
    )

    if r.status_code != 200:
        raise requests.RequestException(f"Received status code {r.status_code}!")

    return r.json()


def get_assets(policy_id: str, epoch_number: int, stake_address: str = None) -> dict:
    if stake_address is None:
        r = requests.get(f"{SNAPSHOTTER_ENDPOINT}/assets/{policy_id}/{epoch_number}")
    else:
        r = requests.get(
            f"{SNAPSHOTTER_ENDPOINT}/assets/{policy_id}/{epoch_number}?stake_address={stake_address}"
        )

    if r.status_code != 200:
        raise requests.RequestException(f"Received status code {r.status_code}!")

    return r.json()

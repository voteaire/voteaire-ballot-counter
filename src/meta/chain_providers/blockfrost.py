from __future__ import annotations

from dotenv import load_dotenv
from blockfrost import BlockFrostApi, ApiError
from lib.cache import cache

import logging
import os

load_dotenv()

BLOCKFROST_KEY = os.getenv("BLOCKFROST_PROJECT_ID")
BLOCKFROST_API_URL = os.getenv("BLOCKFROST_API_URL")

if BLOCKFROST_KEY is None:
    raise TypeError("Blockfrost project ID not defined")

if BLOCKFROST_API_URL is None:
    raise TypeError("Blockfrost API URL not defined")

# Requires BLOCKFROST_PROJECT_ID and BLOCKFROST_API_URL to be set
api = BlockFrostApi(project_id=BLOCKFROST_KEY, base_url=BLOCKFROST_API_URL)

try:
    api.health()
except Exception as e:
    logging.warning("Health check failed for blockfrost")
    logging.warning(e)


# Returns an array of json objects { "tx_hash": "<HASH>"", "json_metadata": "<meta>"}


def get_metadata_entries(label: str, count: int = None, page: int = None):
    if count is None:
        count = 100
    if page is None:
        page = 1

    # TODO replace with paged iterator instance
    # logging.warning("returning metadata - ONLY FIRST PAGE!")

    try:
        metadata_labels = cache.get(f"{label}_{count}_{page}_metadata_labels")
        if metadata_labels is None:
            metadata_labels = api.metadata_label_json(
                label, count=count, page=page, return_type="json", order="asc"
            )
            cache.set(f"{label}_{count}_{page}_metadata_labels", metadata_labels, 60)

    except ApiError as error_json:
        if error_json.status_code == 404:
            logging.warning(f"Page {page} does not exist for label {label}")

            return None
        else:
            raise ApiError(error_json)

    return metadata_labels


# Maybe cache this?
def get_transaction_info(tx_hash):
    return api.transaction(tx_hash, return_type="json")


def get_transaction_inputs(tx_hash):
    tx = api.transaction_utxos(tx_hash, return_type="json")

    if tx is None:
        logging.warning(f"Invalid tx hash {tx_hash}")
        return None
    elif not "inputs" in tx:
        logging.warning(
            "Blockfrost API spec changed, inputs field not found in transaction utxos"
        )
        return None
    else:
        return tx["inputs"]


def get_transaction_outputs(tx_hash):
    tx = api.transaction_utxos(tx_hash, return_type="json")

    if tx is None:
        logging.warning(f"Invalid tx hash {tx_hash}")
        return None
    elif not "outputs" in tx:
        logging.warning(
            "Blockfrost API spec changed, outputs field not found in transaction utxos"
        )
        return None

    return tx["outputs"]


# TODO: Test this function
def get_lovelace_sent(tx_hash, receiving_address):
    outputs = get_transaction_outputs(tx_hash)

    if outputs is not None:
        value = 0
        for output in outputs:
            if not "address" in output:
                logging.warning(
                    "Blockfrost API spec changed, address field not found in outputs"
                )
                return None

            if output["address"] == receiving_address:
                if not "amount" in output:
                    logging.warning(
                        "Blockfrost API spec changed, amount field not found in outputs"
                    )
                    return None

                for asset in output["amount"]:
                    if asset["unit"] == "lovelace":
                        value += int(asset["quantity"])

        return value

    return None


def get_sender_address(tx_hash):
    inputs = get_transaction_inputs(tx_hash)

    if inputs is not None:
        return inputs[0]["address"]

    return None


def get_address_info(address):
    return api.address(address, return_type="json")


def get_epoch_snapshot(staking_address, epoch_no):
    for page in range(1, 4):
        epochs = api.account_history(
            staking_address, order="desc", page=page, return_type="json"
        )

        if page == 1 and epochs == []:
            logging.info(
                "Failed to get snapshot epoch: User staking account is not active!"
            )
            return None

        current_epoch = next(
            (epoch for epoch in epochs if epoch["active_epoch"] == epoch_no), None
        )

        if current_epoch is not None:
            return current_epoch

    logging.info(
        "Failed to get snapshot epoch: Either snapshot doesn't exist or user didn't register before epoch!"
    )
    return None


current_epoch_timeout = 5 * 60


def get_current_epoch():
    current_epoch = cache.get("current_epoch")
    if current_epoch is None:
        current_epoch = api.epoch_latest(return_type="json")
        cache.set("current_epoch", current_epoch, current_epoch_timeout)

    return current_epoch


def get_protocol_parameters():
    current_epoch = get_current_epoch()["epoch"]

    return api.epoch_latest_parameters(number=current_epoch, return_type="json")

from dotenv import load_dotenv
from os import getenv

import pycardano as pyc
import logging


def get_epoch_start_date(epoch: int) -> int:
    load_dotenv()
    network_mode = getenv("NETWORK_MODE")
    if network_mode is None:
        raise ValueError("Undefined network mode!")
    elif network_mode == "TESTNET":
        base_epoch = 10
        base_epoch_start_date = 1658361600
        epoch_duration = 432000
    elif network_mode == "MAINNET":
        base_epoch = 209
        base_epoch_start_date = 1596491091
        epoch_duration = 432000

    return base_epoch_start_date + (epoch - base_epoch) * epoch_duration


def get_epoch_end_date(epoch: int) -> int:
    load_dotenv()
    network_mode = getenv("NETWORK_MODE")
    if network_mode is None:
        raise ValueError("Undefined network mode!")
    elif network_mode == "TESTNET":
        base_epoch = 10
        base_epoch_end_date = 1658793600
        epoch_duration = 432000
    elif network_mode == "MAINNET":
        base_epoch = 209
        base_epoch_end_date = 1596923091
        epoch_duration = 432000
        logging.info("calculating end epoch - in Mainnet mode")
        

    return base_epoch_end_date + (epoch - base_epoch) * epoch_duration


def get_epoch_slot(epoch: int, start=True) -> int:
    # Since Shelley, the epoch duration is 432_000 slots, each is slot is
    # equal to 1 second, but before that 1 slot was 20 seconds, this could
    # change in the future, our calculations assume that this value will
    # remain constant.

    load_dotenv()
    network_mode = getenv("NETWORK_MODE")

    if network_mode.upper() == "TESTNET":
        base_epoch = 10
        base_epoch_start_slot = 2_678_400
        epoch_duration = 432_000
    elif network_mode.upper() == "MAINNET":
        base_epoch = 209
        base_epoch_start_slot = 4_924_800
        epoch_duration = 432_000
    else:
        raise ValueError(f"Invalid network mode: {network_mode}")

    slot = base_epoch_start_slot + (epoch - base_epoch) * epoch_duration

    if start is False:
        return slot + epoch_duration
    
    return slot

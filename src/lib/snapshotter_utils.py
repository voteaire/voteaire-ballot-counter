from typing import Dict, List, Union

import requests
import pycardano as pyc


def add_balances(balances: List[Dict[str, int]]) -> Dict[str, int]:
    """Add a list of balances together

    Args:
        balances (List[Dict[str, int]]): A list of balances.

    Returns:
        Dict[str, int]: The sum of the balances.
    """

    total_balance = {}

    for balance in balances:
        for token, amount in balance.items():
            if token in total_balance:
                total_balance[token] += amount
            else:
                total_balance[token] = amount

    return total_balance


def add_values(
    values: List[Dict[str, Union[int, Dict[str, int]]]]
) -> Dict[str, Union[int, Dict[str, int]]]:
    """Add a list of values together

    Args:
        values (List[Dict[str, Union[int, Dict[str, int]]]]): A list of values.

    Returns:
        Dict[str, Union[int, Dict[str, int]]]: The sum of the values.
    """

    total_value = {"coins": 0, "assets": {}}

    for value in values:
        total_value["coins"] += value["coins"]
        total_value["assets"] = add_balances([total_value["assets"], value["assets"]])

    return total_value


def get_snapshot(
    kupo_endpoint: str, kupo_port: int, address: str, snapshot_time: int
) -> Dict[str, int]:
    """Get the balance of an address at a specific point in time

    Args:
        kupo_endpoint (str): The Kupo endpoint to use.
        kupo_port (int): The Kupo port to use.
        address (str): The address of the user.
        snapshot_time (int): The timestamp of the snapshot.

    Returns:
        Dict[str, int]: The balance of the address at the snapshot time.
    """

    pyc_address = pyc.Address.from_primitive(address)
    parsed_address = ""

    if pyc_address.payment_part is not None and pyc_address.staking_part is not None:
        parsed_address = (
            f"{str(pyc_address.payment_part)}/{str(pyc_address.staking_part)}"
        )
    elif pyc_address.payment_part is not None:
        parsed_address = f"{str(pyc_address.payment_part)}/*"
    elif pyc_address.staking_part is not None:
        parsed_address = f"*/{str(pyc_address.staking_part)}"

    # Get transactions from this address which were spent after the snapshot time and created before
    response = requests.get(
        f"{kupo_endpoint}:{kupo_port}/matches/{parsed_address}?spent_after={snapshot_time}&created_before={snapshot_time}"
    )

    current_slot = int(response.headers["X-Most-Recent-Checkpoint"])

    if current_slot < snapshot_time:
        print("Snapshot time is too far in the future")
        return None

    transactions = response.json()

    total_value = {"coins": 0, "assets": {}}

    for transaction in transactions:
        total_value = add_values([total_value, transaction["value"]])

    # Get transactions from this address which are unspent and were created before the snapshot time
    response = requests.get(
        f"{kupo_endpoint}:{kupo_port}/matches/{parsed_address}?unspent&created_before={snapshot_time}"
    )

    transactions = response.json()

    for transaction in transactions:
        total_value = add_values([total_value, transaction["value"]])

    # In summary, the snapshot of an address is equal to the sum of all the
    # values from the transactions which were created before the snapshot
    # and are either unspent or were spent after the snapshot.

    return total_value
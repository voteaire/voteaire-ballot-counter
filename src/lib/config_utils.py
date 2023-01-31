import datetime
import logging
import json
import time

from model.config import Config
from model import db
from typing import Any, List

configs = {}


def get_config_value(config_key: str) -> Any:
    config_entry: Config | None = Config.query.filter(
        Config.config_key == config_key
    ).first()

    if config_entry is None:
        raise ValueError(f"Config key {config_key} does not exist!")

    now = datetime.datetime.now()
    if config_key in configs and now < configs[config_key]["expire_date"]:
        return configs[config_key]["config_value"]

    # Getting the value and converting it to the right type
    if config_entry.config_type == "str":
        config_value = config_entry.config_value
    elif config_entry.config_type == "int":
        config_value = int(config_entry.config_value)
    elif config_entry.config_type == "bool":
        if config_entry.config_value.lower() == "true":
            config_value = True
        elif config_entry.config_value.lower() == "false":
            config_value = False
        else:
            raise ValueError(f"Cannot convert config value {config_value} to boolean!")
    elif config_entry.config_type == "json":
        config_value = json.loads(config_entry.config_value)
    elif config_entry.config_type == "datetime":
        config_value = datetime.datetime.strptime(
            config_entry.config_value, "%Y-%m-%dT%H:%M:%S%z"
        )
    else:
        raise ValueError(
            f"Type {config_entry.config_type} of config {config_entry.config_key} does not exist!"
        )

    configs[config_entry.config_key] = {
        "config_value": config_value,
        "expire_date": datetime.datetime.now()
        + datetime.timedelta(seconds=config_entry.caching_interval),
    }

    return config_value


def insert_config(
    config_key: str, config_value: str, config_type: str, caching_interval: int
):
    config = Config()
    config.config_key = config_key
    config.config_value = config_value
    config.config_type = config_type
    config.caching_interval = caching_interval

    db.session.add(config)
    db.session.commit()


def get_fees(ballot_type: str) -> int:
    return get_config_value(f"{ballot_type.lower()}_fees")


def wait_for_configs():
    with open("config_requirements.txt", "r") as expected_configs_file:
        expected_configs = expected_configs_file.readlines()

    while True:
        all_passed = True
        for config in expected_configs:
            try:
                value = get_config_value(config.strip())
            except ValueError:
                
                all_passed = False

                logging.warning(
                    f"Config key {config.strip()} not found! Make sure you add it to the database!"
                )

        if all_passed is True:
            return

        time.sleep(3)

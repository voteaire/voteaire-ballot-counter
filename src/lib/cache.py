import logging
from typing import Any
from time import time


class Cache(object):
    def __init__(self):
        self.cached = {}

    def clean_memory(self):
        for key in list(self.cached.keys()):
            if time() > (self.cached[key]["update_date"] + self.cached[key]["timeout"]):
                logging.info(f"Timeout expired for cached key {key}")

                del self.cached[key]

    def get(self, key: str) -> Any:
        """Returns None if the timeout has passed or there is no
        such key. Otherwise it returns the value from cached dictionary"""

        self.clean_memory()

        if not key in self.cached:
            logging.info(f"Key not found in dictionary {key}")

            return None

        return self.cached[key]["value"]

    def set(self, key: str, value: Any, timeout: int):
        self.cached[key] = {"value": value, "timeout": timeout, "update_date": time()}

    def get_or_set(self, key: str, expr: Any, timeout: int, context: str = None):
        key = f"{context}_{key}" if context else key

        expected_value = self.get(key)

        if expected_value is None:
            expected_value = expr()
            cache.set(key, expected_value, timeout)

        return expected_value


cache = Cache()

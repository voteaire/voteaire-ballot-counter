from __future__ import annotations

from dotenv import load_dotenv
from blockfrost import BlockFrostApi, ApiError

import logging
import psycopg2
import os

load_dotenv()


class DBSyncConnectionError(Exception):
    pass


DBSYNC_CONNECTION = os.getenv("DBSYNC")

if DBSYNC_CONNECTION is None:
    raise TypeError("DBSync connection not defined")

db = psycopg2.connect(DBSYNC_CONNECTION, connect_timeout=3)

attempts = 10
worked = False
for i in range(attempts):
    with db.cursor() as cursor:
        cursor.execute("SELECT 1;")
        result = cursor.fetchone()[0]

        if result == 1:
            worked = True
            break
        else:
            logging.warn(f"Attempt {i+1} - DBSync database is not working!")

if not worked:
    raise DBSyncConnectionError(f"DBSync failed to start after {attempts} attempts!")


def get_metadata_entries(label: str, count: int = None, page: int = None):
    if count is None:
        count = 100
    if page is None:
        page = 1

    page_size = 100

    with db.cursor() as cursor:
        cursor.execute("SELECT COUNT(id) FROM tx_metadata WHERE key = %s;", (label,))
        size = cursor.fetchone()[0]

        if (page - 1) * page_size >= size:
            logging.warning(f"Page {page} does not exist for label {label}")

            return None

        cursor.execute(
            """
            SELECT encode(tx.hash, 'hex'), tx_metadata.json
                FROM tx_metadata
                INNER JOIN tx ON tx.id = tx_metadata.tx_id
                WHERE key = %s LIMIT %s OFFSET %s;
        """,
            (label, count, page_size * (page - 1)),
        )

        metadatas = cursor.fetchall()

    return [
        {"tx_hash": tx_hash, "json_metadata": json_metadata}
        for tx_hash, json_metadata in metadatas
    ]


def get_transaction_info(tx_hash):
    pass


def get_transaction_inputs(tx_hash):
    pass


def get_transaction_outputs(tx_hash):
    pass


def get_lovelace_sent(tx_hash, receiving_address):
    pass


def get_sender_address(tx_hash):
    pass


def get_address_info(address):
    pass


def get_epoch_snapshot(staking_address, epoch_no):
    pass


def get_current_epoch():
    pass


def get_protocol_parameters():
    pass

from __future__ import annotations
import sys

import requests
import os

from integration.fixtures import session
from dotenv import load_dotenv

load_dotenv()

BLOCKFROST_KEY = os.getenv("BLOCKFROST_PROJECT_ID")
BLOCKFROST_API_URL = os.getenv("BLOCKFROST_API_URL")
LABEL = os.getenv("LABEL", 1916)


def test_blockfrost(session):
    sys.path.append("src")

    from meta.queue_providers.blockfrost_queue_provider import BlockfrostQueueProvider

    response = requests.get(
        f"{BLOCKFROST_API_URL}/v0/metadata/txs/labels/{LABEL}?page=1&order=asc",
        headers={"project_id": BLOCKFROST_KEY},
    )

    assert response.status_code == 200

    page_1 = response.json()
    assert type(page_1) == list

    queue_provider = BlockfrostQueueProvider()
    for i in range(0, len(page_1)):
        current = queue_provider.next()

        print("------------- Got -------------")
        print(current)

        print()

        print("------------- Expected -------------")
        print(page_1[i])
        assert current == page_1[i]

    # TODO: test other pages
    # Won't be None if we have more than one page
    assert queue_provider.next() is None

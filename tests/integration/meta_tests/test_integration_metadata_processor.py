# Get page 1 blockfrost metadata entries
# For each entry
#   See if they are valid votes, proposal or are just invalid
#   Make sure metadata processor performs accoring to this (their validity)
# After everything has been processed
#   Add one new tx with a new proposal metadata entry
#   Add one new tx with a new vote metadata entry
#   Add one new tx with a new invalid metadata entry
# Make sure they are successfully and correctly processed

# Problems with this approach (migh have lots of entries in
# the future and it would take too long to process everything)

# Solution is to somehow skip the other metadata entries

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


def test_metadata_processor(session):
    sys.path.append("src")

    from meta.queue_providers.blockfrost_queue_provider import BlockfrostQueueProvider

    # Create txs with proposal, vote and invalid metadata entries

    # Run next once (loads first page)
    # Are our entries in this page?
    #   Find out by looking for our IDs
    # If so, mark everything as processed excpet our entries
    # Otherwise, mark everything as processed and load next page
    # Repeat until we get 404 (raise exception) or find our entries
    # When we find our entries make sure metadata processor, processes it correctly

    # while True:
    #     response = requests.get(f"{BLOCKFROST_API_URL}/v0/metadata/txs/labels/{LABEL}?page=1&order=asc",
    #                     headers={'project_id': BLOCKFROST_KEY})

    #     assert response.status_code == 200

    # page_1 = response.json()
    # assert type(page_1) == list

    # queue_provider = BlockfrostQueueProvider()

    # for i in range(0, len(page_1)):
    #     current = queue_provider.next()

    #     print("------------- Got -------------")
    #     print(current)

    #     print()

    #     print("------------- Expected -------------")
    #     print(page_1[i])
    #     assert current == page_1[i]

    # # TODO: test other pages
    # # Won't be None if we have more than one page
    # assert queue_provider.next() is None

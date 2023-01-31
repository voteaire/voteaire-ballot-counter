import importlib
import sys
import logging
from typing import List

from unit.api.fixtures import api


def test_load_page(mocker, api, monkeypatch):
    client, app = api

    sys.path.append("src")

    # This is required for some reason???
    # app.py should be doing this already
    from model import db
    from model.blockfrost_queue import BlockfrostQueue

    with app.app_context():
        db.create_all()

    from model.blockfrost_queue import BlockfrostQueue
    from meta.chain_providers import mock as mock_cp

    monkeypatch.setattr(
        "meta.queue_providers.blockfrost_queue_provider.blockfrost", mock_cp
    )

    from meta.queue_providers.blockfrost_queue_provider import BlockfrostQueueProvider

    queue_prov = BlockfrostQueueProvider()

    with app.app_context():
        queue_prov.load_page(1)

        assert BlockfrostQueue.query.count() == 100

        rows: List[BlockfrostQueue] = BlockfrostQueue.query.all()
        for i, row in zip(range(100), rows):
            assert row.page == 1
            assert row.index == i + 1
            assert row.tx_hash == f"HASH1-{i+1}"
            assert row.json_metadata == {"foo": f"bar1-{i+1}"}

        # Clear table, so we can test one more page
        BlockfrostQueue.query.delete()
        db.session.commit()

        queue_prov.load_page(2)

        assert BlockfrostQueue.query.count() == 100

        rows: List[BlockfrostQueue] = BlockfrostQueue.query.all()
        for i, row in zip(range(100), rows):
            assert row.page == 2
            assert row.index == i + 1
            assert row.tx_hash == f"HASH2-{i+1}"
            assert row.json_metadata == {"foo": f"bar2-{i+1}"}

        # Clear table, so we can test one more page
        BlockfrostQueue.query.delete()
        db.session.commit()

        # We have a max page of 10 in our mock chain provider
        # If we ask for entries from page 11, it should do nothing

        queue_prov.load_page(11)

        assert BlockfrostQueue.query.count() == 0


def test_next(mocker, api, monkeypatch, caplog):
    caplog.set_level(logging.INFO)

    client, app = api

    sys.path.append("src")

    # This is required for some reason???
    # app.py should be doing this already
    from model import db
    from model.blockfrost_queue import BlockfrostQueue

    with app.app_context():
        db.create_all()

    from model.blockfrost_queue import BlockfrostQueue
    from meta.chain_providers import mock as mock_cp

    monkeypatch.setattr(
        "meta.queue_providers.blockfrost_queue_provider.blockfrost", mock_cp
    )

    from meta.queue_providers.blockfrost_queue_provider import BlockfrostQueueProvider

    queue_prov = BlockfrostQueueProvider()

    with app.app_context():
        assert queue_prov.next() == {
            "tx_hash": "HASH1-1",
            "json_metadata": {"foo": "bar1-1"},
        }
        assert BlockfrostQueue.query.count() == 100
        assert (
            BlockfrostQueue.query.filter(BlockfrostQueue.status == "processed").count()
            == 0
        )

        queue_prov.ack("HASH1-1")

        processed = BlockfrostQueue.query.filter(
            BlockfrostQueue.status == "processed"
        ).first()
        assert processed.tx_hash == "HASH1-1"

        assert queue_prov.next() == {
            "tx_hash": "HASH1-2",
            "json_metadata": {"foo": "bar1-2"},
        }

        assert queue_prov.next() == {
            "tx_hash": "HASH1-3",
            "json_metadata": {"foo": "bar1-3"},
        }

        queue_prov.ack("HASH1-3")

        hash_13 = BlockfrostQueue.query.filter(
            BlockfrostQueue.tx_hash == "HASH1-3"
        ).first()

        assert hash_13.status == "processed"

        # Since HASH1-2 wasn't acknowledged, should not be processed in the DB
        hash_12 = BlockfrostQueue.query.filter(
            BlockfrostQueue.tx_hash == "HASH1-2"
        ).first()

        assert hash_12.status == "queued"

        assert queue_prov.next() == {
            "tx_hash": "HASH1-4",
            "json_metadata": {"foo": "bar1-4"},
        }
        queue_prov.ack("HASH1-4")

        hash_14 = BlockfrostQueue.query.filter(
            BlockfrostQueue.tx_hash == "HASH1-4"
        ).first()

        assert hash_14.status == "processed"

        for i in range(5, 101):
            assert queue_prov.next() == {
                "tx_hash": f"HASH1-{i}",
                "json_metadata": {"foo": f"bar1-{i}"},
            }

            queue_prov.ack(f"HASH1-{i}")

        # Why is there still 1 entries and what is it?

        # Load second page
        for i in range(1, 101):
            assert queue_prov.next() == {
                "tx_hash": f"HASH2-{i}",
                "json_metadata": {"foo": f"bar2-{i}"},
            }

            queue_prov.ack(f"HASH2-{i}")

        # Load first element from third page, when page is already loaded
        queue_prov.load_page(3)
        for i in range(1, 101):
            assert queue_prov.next() == {
                "tx_hash": f"HASH3-{i}",
                "json_metadata": {"foo": f"bar3-{i}"},
            }

            queue_prov.ack(f"HASH3-{i}")

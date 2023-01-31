#  a queue provider should implement 2 methods, next() and ack()
# next will provide the next record to process, or None if there are none
# records are {tx_hash, metadata}

from __future__ import annotations

from meta.chain_providers import blockfrost

import logging
import os
import newrelic.agent

from dotenv import load_dotenv
from model import db
from model.blockfrost_queue import BlockfrostQueue
from sqlalchemy import func, and_, not_

load_dotenv()

LABEL = os.environ.get("LABEL", "1916")


class BlockfrostQueueProvider:
    @newrelic.agent.background_task()
    def __init__(self):
        self.queued = set()

    @newrelic.agent.background_task()
    def load_page(self, page: int):
        existing_entries: BlockfrostQueue | None = BlockfrostQueue.query.filter(
            BlockfrostQueue.page == page
        ).count()

        # Possible reason was that I started caching metadata entries results
        # and sometimes if I asked for page 3 I could receive page 2 instead

        if existing_entries == 100:
            # If we already have entries with this page, we can ignore
            return

        entries: list = blockfrost.get_metadata_entries(LABEL, page=page)

        if entries is None:
            # If entries is None it means this page doesn't exist,
            # so we can ignore
            return

        rows = []
        i = existing_entries
        for entry in entries[existing_entries:]:
            blockfrost_queue = BlockfrostQueue()

            blockfrost_queue.page = page
            blockfrost_queue.index = i + 1
            blockfrost_queue.tx_hash = entry["tx_hash"]
            blockfrost_queue.json_metadata = entry["json_metadata"]

            rows.append(blockfrost_queue)

            i += 1

        if len(rows) > 0:
            db.session.add_all(rows)
            db.session.commit()

    @newrelic.agent.background_task()
    def next(self) -> dict | None:
        queued_count = BlockfrostQueue.query.filter(
            and_(
                BlockfrostQueue.status == "queued",
                not_(BlockfrostQueue.tx_hash.in_(self.queued)),
            )
        ).count()

        logging.info(
            f"Loading next queue entry - Remaining queued count {queued_count}"
        )
        if queued_count == 0:
            # If we don't have any unprocessed entry loaded in the DB

            # Get the last page loaded into the DB
            last_row = BlockfrostQueue.query.order_by(
                BlockfrostQueue.page.desc()
            ).first()

            if last_row is None:
                # If we don't have any pages loaded to the DB,
                # load the first one

                self.load_page(1)
            else:
                # If we do have pages loaded to the DB, load
                # the next one (after the last)

                count = BlockfrostQueue.query.filter(
                    BlockfrostQueue.page == last_row.page
                ).count()

                if count == 100:
                    self.load_page(last_row.page + 1)
                else:
                    self.load_page(last_row.page)

        first_unprocessed_row: BlockfrostQueue | None = (
            BlockfrostQueue.query.filter(
                and_(
                    BlockfrostQueue.status == "queued",
                    not_(BlockfrostQueue.tx_hash.in_(self.queued)),
                )
            )
            .order_by(BlockfrostQueue.page.asc(), BlockfrostQueue.index.asc())
            .first()
        )

        if first_unprocessed_row is None:
            logging.info("No more entries found!")

            return None
        else:
            logging.info(f"Entry loaded - {first_unprocessed_row.tx_hash}")

            self.queued.add(first_unprocessed_row.tx_hash)

            return {
                "tx_hash": first_unprocessed_row.tx_hash,
                "json_metadata": first_unprocessed_row.json_metadata,
            }

    @newrelic.agent.background_task()
    def ack(self, tx_hash):
        # We only change the status of the first entry when in reality we have duplicate entries
        item = BlockfrostQueue.query.filter(BlockfrostQueue.tx_hash == tx_hash).first()
        item.status = "processed"

        db.session.add(item)
        db.session.commit()

        logging.info(f"Acknowledged {tx_hash}")

        self.queued.remove(tx_hash)

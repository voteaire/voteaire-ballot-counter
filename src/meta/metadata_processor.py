from __future__ import annotations

import os
import json
import datetime
import logging
import inspect
import copy
import traceback
import newrelic.agent

from lib import schema_validator as sv
from lib import metadata_utils, processor_utils

from dotenv import load_dotenv
from sqlalchemy import func
from meta.vote_weighter import *
from meta.vote_counter import VoteCounter
from model.processed_log import ProcessedLog
from model.proposal import Proposal
from model.question import Question
from model.vote import Vote

from model.choice import Choice

from model.vote_choice import VoteChoice

load_dotenv()

LABEL = os.environ.get("LABEL", "1916")
PLATFORM_ADDRESS = os.environ.get("PLATFORM_ADDRESS", "addr_test")

logging.debug("Initializing metadata processor with:")
logging.debug(f" * LABEL: {LABEL}")
logging.debug(f" * PLATFORM_ADDRESS: {PLATFORM_ADDRESS}")


class MetadataProcessor:
    """MetadataProcessor is the class which is handed a hunk of metadata, and w"""

    def __init__(self, chain_provider, db_session):

        self.chain_provider = chain_provider
        self.db_session = db_session

    @newrelic.agent.background_task()
    def process_metadata_entry(
        self, tx_hash, metadata, chain_provider=None, db_session=None
    ):
        logging.info(f"processing metadata entry - {tx_hash}")

        # votes should be more common, make this default case
        if sv.validate_vote(metadata):
            logging.info("matched vote schema validation")
            self.process_vote(tx_hash, metadata, chain_provider, db_session)
        elif sv.validate_proposal(metadata):
            logging.info("matched proposal schema validation ")
            self.process_proposal(tx_hash, metadata, chain_provider, db_session)
        else:
            message = f"tx {tx_hash} matched nothing, logging invalid"
            logging.warning(message)

            self.process_invalid(
                tx_hash,
                metadata,
                details=message,
                chain_provider=chain_provider,
                db_session=db_session,
            )

    @newrelic.agent.background_task()
    def process_proposal(
        self, tx_hash, metadata, chain_provider=None, db_session=None, overwrite=False
    ):
        if chain_provider == None:
            chain_provider = self.chain_provider
        if db_session == None:
            db_session = self.db_session
        logging.info(f"processing proposal")

        # There should not be such a thing as an invalid vote or proposal
        # They should only be added to the database if they are valid
        # We can keep a history of invalid attempts with process log

        try:
            # Get proposal with given proposal identifier
            proposal = Proposal.query.filter(
                Proposal.proposal_identifier == metadata["ProposalId"]
            ).first()

            result = processor_utils.validate_proposal(
                proposal, metadata, tx_hash, chain_provider, overwrite
            )

            if result["valid"] is False:
                db_session.rollback()

                self.process_invalid(
                    tx_hash,
                    metadata,
                    details=result["message"],
                    chain_provider=chain_provider,
                    db_session=db_session,
                )
            elif result["valid"] is True:
                db_session.add(result["proposal"])
                db_session.commit()

                self.process_valid(
                    tx_hash,
                    metadata,
                    details=None if not "details" in result else result["details"],
                    proposal_id=result["proposal"].id,
                    chain_provider=chain_provider,
                    db_session=db_session,
                )

        except Exception:
            error = traceback.format_exc()

            logging.critical(error)
            self.process_unsuccessful(
                tx_hash,
                metadata,
                details=error,
                chain_provider=chain_provider,
                db_session=db_session,
            )

    #################################
    # Process Vote
    #################################

    @newrelic.agent.background_task()
    def process_vote(
        self, tx_hash, metadata, chain_provider=None, db_session=None, overwrite=False
    ):
        if chain_provider == None:
            chain_provider = self.chain_provider
        if db_session == None:
            db_session = self.db_session
        logging.info(f"processing vote")
        if chain_provider == None:
            chain_provider = self.chain_provider
        if db_session == None:
            db_session = self.db_session

        try:
            # Get vote from DB if it exists
            vote: Vote | None = Vote.query.filter(
                Vote.vote_identifier == metadata["VoteId"]
            ).first()

            with db_session.no_autoflush:
                result = processor_utils.validate_vote(
                    vote, metadata, tx_hash, chain_provider, overwrite
                )

            if result["valid"] is False:
                db_session.rollback()

                self.process_invalid(
                    tx_hash,
                    metadata,
                    details=result["message"],
                    chain_provider=chain_provider,
                    db_session=db_session,
                )
            elif result["valid"] is True:
                db_session.add(result["vote"])
                db_session.commit()

                self.process_valid(
                    tx_hash,
                    metadata,
                    details=None if not "details" in result else result["details"],
                    vote_id=result["vote"].id,
                    chain_provider=chain_provider,
                    db_session=db_session,
                )
        except Exception:
            error = traceback.format_exc()

            logging.critical(error)
            self.process_unsuccessful(
                tx_hash,
                metadata,
                details=error,
                chain_provider=chain_provider,
                db_session=db_session,
            )

    #################################
    # Process Valid
    #################################
    @newrelic.agent.background_task()
    def process_valid(
        self,
        tx_hash,
        metadata,
        details=None,
        proposal_id=None,
        vote_id=None,
        chain_provider=None,
        db_session=None,
    ):
        if (
            chain_provider == None
        ):  # look into table if it finds matching tx and set status to invalid
            chain_provider = self.chain_provider
        if db_session == None:
            db_session = self.db_session

        logging.info(f"Processing valid entry {tx_hash}")

        # create log record
        pl = ProcessedLog()
        pl.tx_hash = tx_hash
        pl.tx_metadata = metadata
        pl.valid = True
        try:
            # look up external info and enrich record
            tx_info = chain_provider.get_transaction_info(tx_hash)
            pl.tx_block_height = tx_info["block_height"]
            pl.tx_datetime = datetime.datetime.utcfromtimestamp(
                int(tx_info["block_time"])
            )

            if details is not None:
                pl.details = details

            if proposal_id is not None:
                pl.proposal_id = proposal_id

            if vote_id is not None:
                pl.vote_id = vote_id

            pl.success = True
        except Exception:
            # error processing, persist to record
            pl.details = traceback.format_exc()
            pl.success = False

        # save
        db_session.add(pl)
        db_session.commit()

    #################################
    # Process Unsuccessful
    #################################
    @newrelic.agent.background_task()
    def process_unsuccessful(
        self, tx_hash, metadata, details, chain_provider=None, db_session=None
    ):
        if (
            chain_provider == None
        ):  # look into table if it finds matching tx and set status to invalid
            chain_provider = self.chain_provider
        if db_session == None:
            db_session = self.db_session

        logging.info(f"Processing invalid entry {tx_hash}")

        # create log record
        pl = ProcessedLog()
        pl.tx_hash = tx_hash
        pl.tx_metadata = metadata
        pl.valid = False
        try:
            # look up external info and enrich record
            tx_info = chain_provider.get_transaction_info(tx_hash)
            pl.tx_block_height = tx_info["block_height"]
            pl.tx_datetime = datetime.datetime.utcfromtimestamp(
                int(tx_info["block_time"])
            )
            pl.details = details
            pl.success = False
        except Exception:
            # error processing, persist to record
            pl.details = traceback.format_exc()
            pl.success = False

        # save
        db_session.add(pl)
        db_session.commit()

    #################################
    # Process Invalid
    #################################
    @newrelic.agent.background_task()
    def process_invalid(
        self, tx_hash, metadata, details=None, chain_provider=None, db_session=None
    ):
        if (
            chain_provider == None
        ):  # look into table if it finds matching tx and set status to invalid
            chain_provider = self.chain_provider
        if db_session == None:
            db_session = self.db_session

        logging.info(f"Processing invalid entry {tx_hash}")
        if details is not None:
            logging.info(f"With error: {details}")

        # create log record
        pl = ProcessedLog()
        pl.tx_hash = tx_hash
        pl.tx_metadata = metadata
        pl.valid = False
        try:
            # look up external info and enrich record
            tx_info = chain_provider.get_transaction_info(tx_hash)
            pl.tx_block_height = tx_info["block_height"]
            pl.tx_datetime = datetime.datetime.utcfromtimestamp(
                int(tx_info["block_time"])
            )
            pl.details = details
            pl.success = True
        except Exception:
            # error processing, persist to record
            pl.details = traceback.format_exc()
            pl.success = False

        # save
        db_session.add(pl)
        db_session.commit()

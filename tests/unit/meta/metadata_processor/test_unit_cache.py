from __future__ import annotations

from meta.metadata_processor import MetadataProcessor
from meta.chain_providers import mock as mock_cp
from unit.meta.db_fixture import session
from model.processed_log import ProcessedLog
from model.proposal import Proposal
from model.config import Config

from sqlalchemy import func

import test_utils
import datetime
import logging
import dotenv

import json
import os


def test_unit_cache(session, monkeypatch):
    dotenv.load_dotenv("src")

    from lib.mock.config_utils import get_fees

    monkeypatch.setattr("lib.config_utils.get_fees", get_fees)

    config = Config()
    config.config_key = "require_fees"
    config.config_value = "true"
    config.config_type = "bool"
    config.caching_interval = 0

    session.add(config)
    session.commit()

    # Value in our mock function for simple type
    lovelace_fees = 10_000_000

    # Simulating we are paying fees
    monkeypatch.setattr(
        "meta.chain_providers.mock.get_lovelace_sent", lambda x, y: lovelace_fees
    )

    m = MetadataProcessor(chain_provider=mock_cp, db_session=session)

    # Draft proposal, paid right fees - SUCCESS

    proposal: Proposal = test_utils.fake_proposal(
        session, source="front-end", status="draft", id=1
    )

    metadata = json.loads(proposal.proposal_metadata)

    # Just to be safe (make sure our DB is not being shared with other tests)
    logs = ProcessedLog.query.all()
    assert len(logs) == 0

    proposals = Proposal.query.all()
    assert len(proposals) == 1

    m.process_proposal(tx_hash="<hash_1>", metadata=metadata)

    logs = ProcessedLog.query.all()
    assert len(logs) == 1

    assert (
        proposal.creator_stake_address
        == "stake_test1ur8tnk9ryc4uw95gw9vde25pzhn5tv6cdyrjf7rmg7e7rns7raxx7"
    )

    # Changing sender address to test whether we are going to cache correctly
    monkeypatch.setattr(
        "meta.chain_providers.mock.get_address_info",
        lambda x: {"stake_address": "stake_test123"},
    )

    m.process_proposal(tx_hash="<hash_1>", metadata=metadata, overwrite=True)

    # Make sure caching is working - Should not return "stake_test123"!

    assert (
        proposal.creator_stake_address
        == "stake_test1ur8tnk9ryc4uw95gw9vde25pzhn5tv6cdyrjf7rmg7e7rns7raxx7"
    )

    # Disabling caching
    monkeypatch.setattr("lib.cache.Cache.get", lambda x, y: None)

    # Makre sure that if we disable cache we actually get the new value

    m.process_proposal(tx_hash="<hash_1>", metadata=metadata, overwrite=True)

    assert proposal.creator_stake_address == "stake_test123"

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


def test_unit_process_proposal_default(session, monkeypatch):
    dotenv.load_dotenv("src")

    from lib.mock.config_utils import get_fees

    monkeypatch.setattr("lib.cache.Cache.get", lambda x, y: None)

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

    resulting_log = logs[0]
    assert resulting_log.valid == True
    assert resulting_log.success == True
    assert resulting_log.details == None

    assert resulting_log.tx_hash == "<hash_1>"
    assert resulting_log.tx_metadata == metadata

    assert (
        resulting_log.tx_block_height
        == mock_cp.get_transaction_info("<hash_1>")["block_height"]
    )
    assert (
        resulting_log.tx_datetime - datetime.datetime(1970, 1, 1)
    ).total_seconds() == mock_cp.get_transaction_info("<hash_1>")["block_time"]

    assert resulting_log.vote_id == None
    assert resulting_log.proposal_id == proposal.id

    assert proposal.proposal_metadata == json.dumps(metadata)
    assert proposal.processed_date is not None
    assert (
        proposal.onchain_date - datetime.datetime(1970, 1, 1)
    ).total_seconds() == mock_cp.get_transaction_info("<hash_1>")["block_time"]

    assert proposal.status == "on-chain"

    config.config_value = "false"
    session.add(config)
    session.commit()

    monkeypatch.setattr(
        "meta.chain_providers.mock.get_lovelace_sent", lambda x, y: lovelace_fees // 2
    )

    proposal: Proposal = test_utils.fake_proposal(
        session, source="front-end", status="draft", id=2
    )

    metadata = json.loads(proposal.proposal_metadata)

    # Just to be safe (make sure our DB is not being shared with other tests)
    logs = ProcessedLog.query.all()
    assert len(logs) == 1

    proposals = Proposal.query.all()
    assert len(proposals) == 2

    m.process_proposal(tx_hash="<hash_1>", metadata=metadata)

    logs = ProcessedLog.query.all()
    assert len(logs) == 2

    resulting_log = logs[1]
    assert resulting_log.valid == True
    assert resulting_log.success == True
    assert resulting_log.proposal_id == proposal.id

    assert proposal.proposal_metadata == json.dumps(metadata)
    assert proposal.status == "on-chain"


def test_unit_process_proposal_no_fees(session, monkeypatch):
    dotenv.load_dotenv("src")

    from lib.mock.config_utils import get_fees

    monkeypatch.setattr("lib.cache.Cache.get", lambda x, y: None)

    monkeypatch.setattr("lib.config_utils.get_fees", get_fees)

    config = Config()
    config.config_key = "require_fees"
    config.config_value = "true"
    config.config_type = "bool"
    config.caching_interval = 0

    session.add(config)
    session.commit()

    lovelace_fees = 10_000_000

    # Simulating we are paying only half the fees
    monkeypatch.setattr(
        "meta.chain_providers.mock.get_lovelace_sent", lambda x, y: lovelace_fees // 2
    )

    m = MetadataProcessor(chain_provider=mock_cp, db_session=session)

    proposal: Proposal = test_utils.fake_proposal(
        session, source="front-end", status="draft", id=1
    )

    metadata = json.loads(proposal.proposal_metadata)

    logs = ProcessedLog.query.all()
    assert len(logs) == 0

    proposals = Proposal.query.all()
    assert len(proposals) == 1

    m.process_proposal(tx_hash="<hash_1>", metadata=metadata)

    logs = ProcessedLog.query.all()
    assert len(logs) == 1

    proposals = Proposal.query.all()
    assert len(proposals) == 1

    resulting_log = logs[0]
    assert resulting_log.valid == False
    assert resulting_log.success == True
    assert resulting_log.details is not None

    new_proposal = proposals[0]

    assert new_proposal.status == "draft"


def test_unit_process_proposal_overwrite(session, monkeypatch):
    dotenv.load_dotenv("src")

    monkeypatch.setattr("lib.cache.Cache.get", lambda x, y: None)

    config = Config()
    config.config_key = "require_fees"
    config.config_value = "false"
    config.config_type = "bool"
    config.caching_interval = 0

    session.add(config)
    session.commit()

    m = MetadataProcessor(chain_provider=mock_cp, db_session=session)

    # Simulate processed proposal
    proposal: Proposal = test_utils.fake_proposal(
        session,
        source="front-end",
        status="on-chain",
        id=1,
        tx_hash="<hash_1>",
        processed_date=func.now(),
        onchain_date=datetime.datetime.utcfromtimestamp(1635505891),
    )

    metadata = json.loads(proposal.proposal_metadata)

    pl = ProcessedLog()

    pl.tx_hash = "<hash_1>"
    pl.tx_metadata = metadata

    pl.valid = True
    pl.success = True

    pl.tx_block_height = 123456
    pl.tx_datetime = datetime.datetime.utcfromtimestamp(1635505891)

    pl.proposal_id = proposal.id

    session.add(pl)
    session.commit()

    logs = ProcessedLog.query.all()
    assert len(logs) == 1

    proposals = Proposal.query.all()
    assert len(proposals) == 1

    # Overwritten proposal
    metadata["ProposalURL"] = "https://notexample.com"

    m.process_proposal(tx_hash="<hash_1>", metadata=metadata, overwrite=True)

    logs = ProcessedLog.query.all()
    assert len(logs) == 2

    proposals = Proposal.query.all()
    assert len(proposals) == 1

    new_log = logs[1]
    assert new_log.valid == True
    assert new_log.success == True
    assert new_log.details == "Overwriting proposal"
    assert new_log.proposal_id == proposal.id

    assert proposal.status == "on-chain"
    assert proposal.proposal_metadata == json.dumps(metadata)


def test_unit_process_proposal_overwritten_fail(session, monkeypatch):
    dotenv.load_dotenv("src")

    monkeypatch.setattr("lib.cache.Cache.get", lambda x, y: None)

    config = Config()
    config.config_key = "require_fees"
    config.config_value = "false"
    config.config_type = "bool"
    config.caching_interval = 0

    session.add(config)
    session.commit()

    m = MetadataProcessor(chain_provider=mock_cp, db_session=session)

    # Simulate processed proposal
    proposal: Proposal = test_utils.fake_proposal(
        session,
        source="front-end",
        status="on-chain",
        id=1,
        tx_hash="<hash_1>",
        processed_date=func.now(),
        onchain_date=datetime.datetime.utcfromtimestamp(1635505891),
    )

    metadata = json.loads(proposal.proposal_metadata)

    pl = ProcessedLog()

    pl.tx_hash = "<hash_1>"
    pl.tx_metadata = metadata

    pl.valid = True
    pl.success = True

    pl.tx_block_height = 123456
    pl.tx_datetime = datetime.datetime.utcfromtimestamp(1635505891)

    session.add(pl)
    session.commit()

    logs = ProcessedLog.query.all()
    assert len(logs) == 1

    proposals = Proposal.query.all()
    assert len(proposals) == 1

    # Simulating overwrite with overwrite=False
    m.process_proposal(tx_hash="<hash_1>", metadata=metadata, overwrite=False)

    logs = ProcessedLog.query.all()
    assert len(logs) == 2

    proposals = Proposal.query.all()
    assert len(proposals) == 1

    new_log = logs[1]

    assert new_log.valid == False
    assert new_log.success == True

    new_log.proposal_id = None
    assert new_log.tx_hash == "<hash_1>"
    assert new_log.tx_metadata == metadata

    assert proposal.status == "on-chain"


def test_unit_process_proposal_manual(session, monkeypatch, caplog):
    caplog.set_level(logging.INFO)

    dotenv.load_dotenv("src")

    monkeypatch.setattr("lib.cache.Cache.get", lambda x, y: None)

    configs = Config.query.all()
    logging.info(configs)

    config = Config()
    config.config_key = "require_fees"
    config.config_value = "false"
    config.config_type = "bool"
    config.caching_interval = 0

    session.add(config)
    session.commit()

    configs = Config.query.all()
    logging.info(configs[0].config_value)

    m = MetadataProcessor(chain_provider=mock_cp, db_session=session)

    # Manually submitted proposal
    proposal: Proposal = test_utils.fake_proposal(session, id=1, add_to_db=False)

    metadata = json.loads(proposal.proposal_metadata)

    logs = ProcessedLog.query.all()
    assert len(logs) == 0

    proposals = Proposal.query.all()
    assert len(proposals) == 0

    m.process_proposal(tx_hash="<hash_1>", metadata=metadata, overwrite=False)

    logs = ProcessedLog.query.all()
    assert len(logs) == 1

    logging.info("beep")
    logging.info(logs[0].details)

    proposals = Proposal.query.all()
    assert len(proposals) == 1

    proposal = proposals[0]
    log = logs[0]

    assert log.valid == True
    assert log.success == True

    assert log.proposal_id == proposal.id
    assert log.tx_hash == "<hash_1>"
    assert log.tx_metadata == metadata

    # TODO: Validate more stuff
    assert proposal.status == "on-chain"


def test_unit_process_proposal_wrong_epoch(session, monkeypatch):
    dotenv.load_dotenv("src")

    from lib.mock.config_utils import get_fees

    monkeypatch.setattr("lib.cache.Cache.get", lambda x, y: None)

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
        session,
        source="front-end",
        status="draft",
        id=1,
        start_epoch=200,
        end_epoch=204,
        snapshot_epoch=202,
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

    resulting_log = logs[0]
    assert resulting_log.valid == False
    assert resulting_log.success == True

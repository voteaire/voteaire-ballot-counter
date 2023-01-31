from __future__ import annotations

from meta.metadata_processor import MetadataProcessor
from meta.chain_providers import mock as mock_cp
from unit.meta.db_fixture import session
from model.processed_log import ProcessedLog
from model.proposal import Proposal

from lib import metadata_utils
from sqlalchemy import func

import datetime
import test_utils

import json

from model.vote import Vote
from model.vote_choice import VoteChoice


def test_unit_process_vote_default(session, monkeypatch):
    # Simulate current epoch to be within start and end date
    # (200, 201) from fake vote
    monkeypatch.setattr(
        "meta.chain_providers.mock.get_current_epoch", lambda: {"epoch": 200}
    )
    monkeypatch.setattr(
        "meta.chain_providers.mock.get_transaction_info",
        lambda _: {"block_height": 123456, "block_time": 1740441600},
    )
    monkeypatch.setattr("lib.cache.Cache.get", lambda x, y: None)

    m = MetadataProcessor(chain_provider=mock_cp, db_session=session)

    vote: Vote = test_utils.fake_vote(session)

    metadata = metadata_utils.get_vote_metadata(vote)

    logs = ProcessedLog.query.all()
    assert len(logs) == 0

    votes = Vote.query.all()
    assert len(votes) == 1

    m.process_vote(tx_hash="<hash_1>", metadata=metadata)

    logs = ProcessedLog.query.all()
    assert len(logs) == 1

    votes = Vote.query.all()
    assert len(votes) == 1

    resulting_log = logs[0]
    assert resulting_log.tx_hash == "<hash_1>"
    assert resulting_log.valid == True
    assert resulting_log.success == True
    assert resulting_log.details == None
    assert resulting_log.tx_metadata == metadata
    assert (
        resulting_log.tx_block_height
        == mock_cp.get_transaction_info("<hash_1>")["block_height"]
    )
    assert (
        resulting_log.tx_datetime - datetime.datetime(1970, 1, 1)
    ).total_seconds() == mock_cp.get_transaction_info("<hash_1>")["block_time"]
    assert resulting_log.vote_id == vote.id
    assert resulting_log.proposal_id == None

    assert vote.vote_metadata == json.dumps(metadata)
    assert vote.processed_date is not None
    assert (
        vote.onchain_date - datetime.datetime(1970, 1, 1)
    ).total_seconds() == mock_cp.get_transaction_info("<hash_1>")["block_time"]


def test_unit_process_vote_invalid_epoch(session, monkeypatch):
    # Simulate current epoch to be before start date 200
    monkeypatch.setattr(
        "meta.chain_providers.mock.get_current_epoch", lambda: {"epoch": 199}
    )
    monkeypatch.setattr(
        "meta.chain_providers.mock.get_transaction_info",
        lambda _: {"block_height": 123456, "block_time": 1740009600},
    )
    monkeypatch.setattr("lib.cache.Cache.get", lambda x, y: None)

    m = MetadataProcessor(chain_provider=mock_cp, db_session=session)

    vote: Vote = test_utils.fake_vote(session)

    metadata = metadata_utils.get_vote_metadata(vote)

    logs = ProcessedLog.query.all()
    assert len(logs) == 0

    votes = Vote.query.all()
    assert len(votes) == 1

    m.process_vote(tx_hash="<hash_1>", metadata=metadata)

    logs = ProcessedLog.query.all()
    assert len(logs) == 1

    votes = Vote.query.all()
    assert len(votes) == 1

    log = logs[0]
    assert log.tx_hash == "<hash_1>"
    assert log.valid == False
    assert log.success == True
    assert log.details == "Vote submitted before start epoch 200!"

    # Simulate current epoch to be after end date 201
    monkeypatch.setattr(
        "meta.chain_providers.mock.get_current_epoch", lambda: {"epoch": 202}
    )
    monkeypatch.setattr(
        "meta.chain_providers.mock.get_transaction_info",
        lambda _: {"block_height": 123456, "block_time": 1741737600},
    )

    m.process_vote(tx_hash="<hash_2>", metadata=metadata)

    logs = ProcessedLog.query.all()
    assert len(logs) == 2

    votes = Vote.query.all()
    assert len(votes) == 1

    log = logs[1]
    assert log.tx_hash == "<hash_2>"
    assert log.valid == False
    assert log.success == True
    assert log.details == "Vote submitted after end epoch 201!"


def test_unit_process_vote_overwrite(session, monkeypatch):
    monkeypatch.setattr(
        "meta.chain_providers.mock.get_current_epoch", lambda: {"epoch": 200}
    )
    monkeypatch.setattr(
        "meta.chain_providers.mock.get_transaction_info",
        lambda _: {"block_height": 123456, "block_time": 1740441600},
    )
    monkeypatch.setattr("lib.cache.Cache.get", lambda x, y: None)

    m = MetadataProcessor(chain_provider=mock_cp, db_session=session)

    vote: Vote = test_utils.fake_vote(
        session,
        source="front-end",
        status="on-chain",
        id=1,
        processed_date=func.now(),
        onchain_date=datetime.datetime.utcfromtimestamp(1740441600),
    )

    metadata = metadata_utils.get_vote_metadata(vote)

    logs = ProcessedLog.query.all()
    assert len(logs) == 0

    votes = Vote.query.all()
    assert len(votes) == 1

    # overwrite
    metadata["ObjectVersion"] = "2.0.0"

    m.process_vote(tx_hash="<hash_2>", metadata=metadata, overwrite=True)

    logs = ProcessedLog.query.all()
    assert len(logs) == 1

    votes = Vote.query.all()
    assert len(votes) == 1

    resulting_log = logs[0]
    assert resulting_log.tx_hash == "<hash_2>"
    assert resulting_log.valid == True
    assert resulting_log.success == True
    assert resulting_log.tx_metadata == metadata

    vote = votes[0]
    assert vote.vote_metadata == json.dumps(metadata)
    assert vote.status == "on-chain"
    assert vote.processed_date is not None


def test_unit_process_vote_manual(session, monkeypatch):
    monkeypatch.setattr(
        "meta.chain_providers.mock.get_current_epoch", lambda: {"epoch": 200}
    )
    monkeypatch.setattr(
        "meta.chain_providers.mock.get_transaction_info",
        lambda _: {"block_height": 123456, "block_time": 1740441600},
    )
    monkeypatch.setattr("lib.cache.Cache.get", lambda x, y: None)

    m = MetadataProcessor(chain_provider=mock_cp, db_session=session)

    proposal: Proposal = test_utils.fake_proposal(
        session, source="front-end", status="on-chain", id=1, tx_hash="<hash_1>"
    )

    question = proposal.questions[0]
    choice = question.choices[0]

    metadata = {
        "ObjectType": "VoteBallot",
        "ObjectVersion": "1.0.0",
        "VoteId": "ef50af96-3a18-4c85-bfb0-eddb968ca26d",
        "ProposalId": proposal.proposal_identifier,
        "Choices": [
            {
                "QuestionId": question.question_identifier,
                "ChoiceId": choice.choice_identifier,
            }
        ],
    }

    logs = ProcessedLog.query.all()
    assert len(logs) == 0

    votes = Vote.query.all()
    assert len(votes) == 0

    m.process_vote(tx_hash="<hash_2>", metadata=metadata)

    logs = ProcessedLog.query.all()
    assert len(logs) == 1

    print(logs[0].details)

    votes = Vote.query.all()
    assert len(votes) == 1

    log = logs[0]
    vote: Vote = votes[0]

    print(log.details)
    assert log.tx_hash == "<hash_2>"
    assert log.valid == True
    assert log.success == True

    assert log.details == None
    assert log.vote_id == vote.id

    assert vote.vote_identifier == "ef50af96-3a18-4c85-bfb0-eddb968ca26d"
    assert vote.version == "1.0.0"
    assert vote.voter_stake_address == mock_cp.get_address_info("addr")["stake_address"]

    assert len(vote.vote_choices) == 1
    vote_choice: VoteChoice = vote.vote_choices[0]

    assert (
        vote_choice.choice.question.question_identifier == question.question_identifier
    )
    assert vote_choice.choice.choice_identifier == choice.choice_identifier

    assert vote.tx_hash == "<hash_2>"
    assert vote.vote_metadata == json.dumps(metadata)
    assert vote.source == "manual"
    assert vote.processed_date is not None
    assert (
        vote.onchain_date - datetime.datetime(1970, 1, 1)
    ).total_seconds() == mock_cp.get_transaction_info("HASH1")["block_time"]

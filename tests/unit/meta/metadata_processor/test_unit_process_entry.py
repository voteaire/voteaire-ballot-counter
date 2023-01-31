import logging
import json

from meta.metadata_processor import MetadataProcessor
from meta.chain_providers import mock as mock_cp
from unit.meta.db_fixture import session
from model.processed_log import ProcessedLog
from unittest.mock import patch


def test_process_metadata_entry(caplog):
    caplog.set_level(logging.INFO)

    m = MetadataProcessor(None, None)
    # proposal
    with open("tests/unit/fixtures/schema_samples/proposal1.json", "r") as f:
        meta = json.loads(f.read())
    with patch.object(m, "process_proposal") as mock:
        result = m.process_metadata_entry("test_tx_hash", meta)
    mock.assert_called()

    # vote
    with open("tests/unit/fixtures/schema_samples/vote1.json", "r") as f:
        meta = json.loads(f.read())
    with patch.object(m, "process_vote") as mock:
        result = m.process_metadata_entry("test_tx_hash2", meta)
    mock.assert_called()

    # invalid
    with open("tests/unit/fixtures/schema_samples/proposal_invalid.json", "r") as f:
        meta = json.loads(f.read())
    with patch.object(m, "process_invalid") as mock:
        result = m.process_metadata_entry("test_tx_hash3", meta)
    mock.assert_called()


def test_process_invalid(caplog, session):
    caplog.set_level(logging.INFO)
    m = MetadataProcessor(chain_provider=mock_cp, db_session=session)
    m.process_invalid("test_hash1", {"foo": "bar"})

    logs = session.query(ProcessedLog).all()
    assert len(logs) == 1
    assert logs[0].tx_hash == "test_hash1"

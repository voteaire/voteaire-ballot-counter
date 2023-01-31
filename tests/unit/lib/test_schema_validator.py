import pytest
import sys
import json

sys.path.append("src")
import lib.schema_validator as sv


import logging


def test_validate_proposal(caplog):
    caplog.set_level(logging.INFO)

    with open("tests/unit/fixtures/schema_samples/proposal1.json", "r") as f:
        data = f.read()
    # parse file
    obj = json.loads(data)
    result = sv.validate_proposal(obj, schemapath="src/model/json_schemas/")
    assert result

    with open("tests/unit/fixtures/schema_samples/proposal_invalid.json", "r") as f:
        data = f.read()
    # parse file
    obj = json.loads(data)
    result = sv.validate_proposal(obj, schemapath="src/model/json_schemas/")
    assert not result


def test_validate_vote(caplog):
    caplog.set_level(logging.INFO)

    with open("tests/unit/fixtures/schema_samples/vote1.json", "r") as f:
        data = f.read()
    # parse file
    obj = json.loads(data)
    result = sv.validate_vote(obj, schemapath="src/model/json_schemas/")
    assert result

    # with open('tests/lib_tests/schema_samples/proposal_invalid.json', 'r') as f:
    #     data=f.read()
    # # parse file
    # obj = json.loads(data)
    # result = sv.validate_proposal(obj)
    # assert(not result)

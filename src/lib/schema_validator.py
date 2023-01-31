import json, os
from jsonschema import validate, Draft4Validator, ValidationError, RefResolver
import logging
import model.json_schemas
import importlib.resources


def validate_proposal(json_val, schemapath=None):
    try:

        if schemapath == None:
            schemapath = "model/json_schemas/"

        # with open(f'{schemapath}ballot_proposal.json', 'r') as f:
        with importlib.resources.open_text(
            "model.json_schemas", "ballot_proposal.json"
        ) as f:
            proposal_schema = json.load(f)

        base = json.loads(
            importlib.resources.open_text(
                "model.json_schemas", "ballot_proposal.json"
            ).read()
        )
        question = json.loads(
            importlib.resources.open_text(
                "model.json_schemas", "ballot_question.json"
            ).read()
        )
        type = json.loads(
            importlib.resources.open_text(
                "model.json_schemas", "ballot_type.json"
            ).read()
        )

        schema_store = {
            base.get("$id", "ballot_proposal.json"): base,
            question.get("$id", "ballot_question.json"): question,
            type.get("$id", "ballot_type.json"): type,
        }

        proposal_resolver = RefResolver.from_schema(base, store=schema_store)

        Draft4Validator.check_schema(proposal_schema)  # Unnecessary but a good idea
        validator = Draft4Validator(
            proposal_schema, resolver=proposal_resolver, format_checker=None
        )
        validator.validate(json_val)
        logging.info("validating document - got here with no error - passing")
        return True
    except ValidationError as e:
        # logging.debug(e)
        return False


def validate_vote(json_val, schemapath=None):
    try:

        if schemapath == None:
            schemapath = "model/json_schemas/"

        with importlib.resources.open_text(
            "model.json_schemas", "voter_ballot.json"
        ) as f:
            vote_schema = json.load(f)

        base = json.loads(
            importlib.resources.open_text(
                "model.json_schemas", "voter_ballot.json"
            ).read()
        )

        schema_store = {base.get("$id", "voter_ballot.json"): base}

        vote_resolver = RefResolver.from_schema(base, store=schema_store)

        Draft4Validator.check_schema(vote_schema)  # Unnecessary but a good idea
        validator = Draft4Validator(
            vote_schema, resolver=vote_resolver, format_checker=None
        )
        validator.validate(json_val)
        logging.info("validating document - got here with no error - passing")
        return True
    except ValidationError as e:
        # logging.debug(e)
        return False

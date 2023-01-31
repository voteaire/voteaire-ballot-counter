import os
import time
import dotenv
import logging
import requests

from model import db
from model.proposal import Proposal
from model.vote import Vote
from model.vote_choice import VoteChoice
from model.choice import Choice
from model.question import Question
from model.processed_log import ProcessedLog
from model.blockfrost_queue import BlockfrostQueue

from lib import signature_utils, cache
from workers import chain

from flask import Flask
from flask_migrate import Migrate

from sqlalchemy import and_, func
from sqlalchemy.orm import sessionmaker

from meta.metadata_processor import MetadataProcessor


CURRENT_EPOCH_CACHE = 60 * 60 * 5  # 5 hours


def count_votes(choice_id):
    total_votes = (
        VoteChoice.query.join(Vote)
        .filter(and_(VoteChoice.choice_id == choice_id, Vote.status == "on-chain"))
        .count()
    )

    total_weight = (
        VoteChoice.query.join(Vote)
        .filter(and_(VoteChoice.choice_id == choice_id, Vote.status == "on-chain"))
        .with_entities(func.sum(Vote.weight).label("weight_sum"))
        .scalar()
    )

    return {"votes_count": total_votes, "votes_weight": total_weight}


def parse_result(result):
    """Convert the voting results into a string with the format
    <weight1question1>,<weight2question1>|<weight1question2>,<weight2question2>,..."""

    result_string = ""
    for question, choices in result.items():
        question_result = ""
        for choice, count in choices.items():
            question_result += f"{count['votes_weight']},"
        question_result = question_result[:-1]
        result_string += f"{question_result}|"

    return result_string[:-1]


def run_submitter_worker(chain_provider, interval=10):
    """A worker that makes a POST request to an arbitrary URL for every proposal which has ended
    with it's voting results"""

    dotenv.load_dotenv()

    while True:
        current_epoch = cache.cache.get_or_set(
            "current_epoch",
            lambda: chain_provider.get_current_epoch()["epoch"],
            CURRENT_EPOCH_CACHE,
        )

        # current_epoch = chain_provider.get_current_epoch()["epoch"]

        # Get all proposals that have ended
        proposals = Proposal.query.filter(
            and_(current_epoch > Proposal.end_epoch, Proposal.status == "on-chain")
        ).all()

        for proposal in proposals:
            logging.info(
                f"Processing submission info for proposal {proposal.proposal_identifier}..."
            )

            result = {}
            for question in proposal.questions:
                result[question.question_identifier] = {}
                for choice in question.choices:
                    count = count_votes(choice_id=choice.id)

                    if count["votes_weight"] is None:
                        count["votes_weight"] = 0
                    if count["votes_count"] is None:
                        count["votes_count"] = 0

                    result[question.question_identifier][
                        choice.choice_identifier
                    ] = count

            proposal.status = "notified"

            db.session.add(proposal)
            db.session.commit()

            secret_key = os.environ.get("ORACLE_SKEY")
            if secret_key is None:
                raise ValueError("ORACLE_SKEY is not set")

            signed_result = signature_utils.sign(
                secret_key[4:], parse_result(result).encode("utf-8").hex()
            )

            logging.warning(
                {
                    "proposal": proposal.proposal_identifier,
                    "result": result,
                    "result_string": parse_result(result),
                    "signed_result": signed_result,
                }
            )

            # # Make a POST request to the URL
            # requests.post(os.environ.get("SUBMITTER_URL"), json=data)

        time.sleep(interval)

"""A worker that makes a POST request to an arbitrary URL for every proposal which has ended
with it's voting results"""

import os
import requests

from model import db
from model.proposal import Proposal
from model.vote import Vote
from model.vote_choice import VoteChoice
from model.choice import Choice
from model.question import Question
from model.processed_log import ProcessedLog
from model.blockfrost_queue import BlockfrostQueue

from lib import config_utils
from workers import chain

from flask import Flask
from flask_migrate import Migrate

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from meta.metadata_processor import MetadataProcessor


def run_submitter_worker(chain_provider):
    """A worker that makes a POST request to an arbitrary URL for every proposal which has ended
    with it's voting results"""

    current_epoch = chain_provider.get_current_epoch()["epoch"]


    # Get all proposals that have ended
    proposals = Proposal.query.filter(Proposal.end_epoch < current_epoch).all()

    results = []
    for proposal in proposals:

        result = {}
        any_is_not_none = False
        for question in proposal.questions:
            for choice in question.choices:

                if proposal.status != "on-chain":
                    choice["choice_votes"] = None
                    choice["choice_weight"] = None

                    del choice["id"]
                else:
                    votes = count_votes(choice_id=choice["id"])

                    del choice["id"]
                    choice["choice_votes"] = votes["votes_count"]
                    choice["choice_weight"] = votes["votes_weight"]

                if choice["choice_weight"] is not None:
                    any_is_not_none = True

        if any_is_not_none:
            for question in result["questions"]:
                for choice in question["responses"]:
                    if choice["choice_weight"] is None:
                        choice["choice_weight"] = 0

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

        # Create a dict with all the data
        data = {
            "proposal": proposal,
            "questions": questions,
            "votes": votes,
            "choices": choices,
            "vote_choices": vote_choices,
            "processed_logs": processed_logs,
            "blockfrost_queues": blockfrost_queues,
        }

        # Make a POST request to the URL
        requests.post(os.environ.get("SUBMITTER_URL"), json=data)
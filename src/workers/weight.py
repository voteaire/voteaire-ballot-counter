import re
import json
import logging
import importlib
import newrelic.agent

from meta.vote_weighter import VoteWeighter
from model.vote import Vote

from sqlalchemy import and_

from time import sleep


def run_weight_worker(session, chain_provider, delay=5):
    # Regex pattern to convert CamelCase to snake_case
    camel_to_snake_pattern = re.compile(r"(?<!^)(?=[A-Z])")

    while True:

        @newrelic.agent.background_task()
        def weight_worker_step():
            # Votes need to have a null weight and need to be on-chain
            votes_queue = (
                Vote.query.filter(
                    Vote.weight == None,
                    Vote.status == "on-chain",  # Search for only votes in the present
                )
                .order_by(Vote.onchain_date.asc())
                .all()
            )

            for vote in votes_queue:
                vote: Vote = vote  # Just type annotating

                weighter_type = vote.proposal.ballot_type

                if weighter_type is None:
                    raise ValueError("OnChain vote has null ballot type!")

                # snake_case version of our weigher type
                weighter_type_snake = camel_to_snake_pattern.sub(
                    "_", weighter_type
                ).lower()

                weighter_class = getattr(
                    importlib.import_module(
                        f"meta.vote_weighter.{weighter_type_snake}"
                    ),
                    f"{weighter_type}VoteWeighter",
                )

                weighter: VoteWeighter = weighter_class()
                logging.info(f"Attempting to weight vote - {weighter_type}")

                if vote.voter_stake_address is None:
                    raise ValueError("OnChain vote has null voter stake address!")

                if vote.proposal.proposal_metadata is None:
                    raise ValueError("OnChain proposal has null metadata!")

                # Check if vote is duplicate
                duplicate_vote = Vote.query.filter(and_(
                    Vote.id != vote.id,
                    Vote.voter_stake_address == vote.voter_stake_address,
                    Vote.proposal_id == vote.proposal_id,
                    Vote.status == "on-chain" #only count votes which actually made it on-chain
                )).first()

                if duplicate_vote is not None:
                    # Doing this validation here instead of vote weighter to simplify if
                    # Otherwise we would need to provide a lot of extra info and also wrap
                    # it in a DB session

                    vote.weight = 0
                    vote.error_message = (
                        f"Found duplicate vote {duplicate_vote.vote_identifier}"
                    )
                    logging.warning(
                        f"Invalidating vote {vote.vote_identifier} with error {vote.error_message}"
                    )
                else:
                    proposal_metadata = json.loads(vote.proposal.proposal_metadata)
                    ballot_type_dict = proposal_metadata["BallotType"]

                    result = weighter.weight_vote(
                        vote.voter_stake_address,
                        vote.proposal.snapshot_epoch,
                        ballot_type_dict,
                        chain_provider,
                    )

                    if result["status"] == "invalid":
                        vote.weight = 0
                        vote.error_message = result["message"]
                        logging.warning(
                            f"Invalidating vote {vote.vote_identifier} with error {vote.error_message}"
                        )
                    elif result["status"] == "success":
                        vote.weight = result["vote_weight"]
                        logging.info(
                            f"Assigning weight of {result['vote_weight']} to vote {vote.vote_identifier}"
                        )
                    elif result["status"] == "future-epoch":
                        logging.info(
                            f"Skiping future epoch vote {vote.vote_identifier}"
                        )
                    elif result["status"] == "error":
                        logging.critical(result["message"])
                    else:
                        raise ValueError(
                            f"Unidentified status {result['status']} for vote {vote.vote_identifier}"
                        )

                session.add(vote)
                session.commit()

        weight_worker_step()
        logging.info("Weight Worker BEEP!")
        sleep(delay)

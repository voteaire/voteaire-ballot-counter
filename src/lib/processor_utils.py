from __future__ import annotations

from model.proposal import Proposal
from model.question import Question
from model.choice import Choice
from model.vote import Vote
from model.vote_choice import VoteChoice

from lib import config_utils, metadata_utils, blockchain_utils
from lib.cache import cache
from sqlalchemy import func
from typing import Any

import datetime
import logging
import dotenv
import json
import os


dotenv.load_dotenv()


# Need to change this fees system
PLATFORM_ADDRESS = os.environ.get("PLATFORM_ADDRESS", "addr_test")


class ProviderError(Exception):
    pass


def validate_proposal(
    proposal: Proposal | None,
    metadata: dict,
    tx_hash: str,
    chain_provider: Any,
    overwrite: bool,
) -> dict:

    # There could be a case where we set overwrite to true,
    # but we do a normal operation (proposal is None), in
    # which case we should ignore overwrite
    overwrite_case = proposal is not None and (
        proposal.status == "on-chain" or proposal.status == "invalid"
    )

    if overwrite_case and overwrite is False:
        logging.warning(
            f"Tried to overwrite proposal {proposal.proposal_identifier} but failed because overwrite = False!"
        )

        return {
            "valid": False,
            "message": f"Tried to overwrite proposal with overwrite = False! Proposal {proposal.proposal_identifier} already exists!",
        }

    if proposal is not None and metadata["ProposalId"] != proposal.proposal_identifier:
        # Actually doesn't make any sense since we got the old
        # proposal by comparing with proposal identifier

        # But doing it just to be safe, maybe we change the code
        # in the future and this could prevent headeaches

        raise ValueError(
            f"Proposal {proposal.proposal_identifier} has different proposal id from metadata {metadata['ProposalId']}!"
        )

    if overwrite_case or proposal is None:
        # If we need to create a proposal row instead of using an existing one
        # (we are overwritting it or we are manually creating it)

        # Create new proposal based on the metadata

        if overwrite_case:
            proposal.source = "overwrite"
        else:
            proposal = Proposal()
            proposal.source = "manual"

        proposal.proposal_identifier = metadata["ProposalId"]
        proposal.version = metadata["ObjectVersion"]
        proposal.network_id = metadata["NetworkId"]

        if "ProposalURL" in metadata:
            proposal.proposal_url = metadata["ProposalURL"]

        proposal.title = metadata["Title"]

        if "Description" in metadata:
            proposal.description = metadata_utils.parse_string_list(
                metadata["Description"]
            )

        proposal.ballot_type = metadata["BallotType"]["Name"]
        proposal.snapshot_epoch = metadata["SnapshotEpoch"]

        # TODO: Test those multiple ballot types
        if proposal.ballot_type == "Delegated":
            proposal.pool_id = metadata["BallotType"]["PoolId"]
        elif proposal.ballot_type == "PolicyId":
            proposal.policy_id = metadata["BallotType"]["PolicyId"]

        exisiting_questions = Question.query.all()

        questions = []
        for question_data in metadata["Questions"]:
            question: Question | None = Question.query.filter(
                Question.question_identifier == question_data["QuestionId"]
            ).first()

            if not overwrite_case and question is not None:
                return {
                    "valid": False,
                    "message": f"Question with question ID {question_data['QuestionId']} already exists!",
                }

            question = Question()

            question.question_identifier = question_data["QuestionId"]
            question.question = metadata_utils.parse_string_list(
                question_data["Question"]
            )
            question.choice_limit = question_data["ChoiceLimit"]

            if "Description" in question_data:
                question.description = metadata_utils.parse_string_list(
                    question_data["Description"]
                )

            choices = []
            for choice_data in question_data["Choices"]:
                choice: Choice | None = Choice.query.filter(
                    Choice.choice_identifier == choice_data["ChoiceId"]
                ).first()

                if not overwrite_case and choice is not None:
                    return {
                        "valid": False,
                        "message": f"Choice with choice ID {choice_data['ChoiceId']} already exists!",
                    }

                choice = Choice()
                choice.choice_identifier = choice_data["ChoiceId"]
                choice.choice = choice_data["Name"]

                if "Description" in choice_data:
                    choice.description = metadata_utils.parse_string_list(
                        choice_data["Description"]
                    )

                choices.append(choice)

            question.choices = choices

            questions.append(question)

        proposal.questions = questions
        proposal.start_epoch = metadata["VoteStartEpoch"]
        proposal.end_epoch = metadata["VoteEndEpoch"]

    if proposal.start_epoch > proposal.end_epoch:
        return {
            "valid": False,
            "message": f"Start epoch {proposal.start_epoch} greater than end epoch {proposal.end_epoch}!",
        }

    if (
        proposal.ballot_type == "PolicyId"
        and proposal.snapshot_epoch > proposal.start_epoch
    ):
        return {
            "valid": False,
            "message": f"Snapshot epoch {proposal.snapshot_epoch} greater than start epoch {proposal.start_epoch} for policy id proposal!",
        }

    elif proposal.snapshot_epoch - 1 > proposal.start_epoch:
        return {
            "valid": False,
            "message": f"Snapshot epoch - 1 {proposal.snapshot_epoch - 1} greater than start epoch {proposal.start_epoch}!",
        }

    # Operations that apply to both cases (manual / front-end)

    # Timeout for all blockfrost operation from now on
    timeout = 1 * 60

    creator_address = cache.get_or_set(
        "creator_address",
        lambda: chain_provider.get_sender_address(tx_hash),
        timeout,
        tx_hash,
    )

    if creator_address is None:
        raise ProviderError(f"Could not get sender address from tx_hash {tx_hash}!")

    address_info = cache.get_or_set(
        "address_info",
        lambda: chain_provider.get_address_info(creator_address),
        timeout,
        tx_hash,
    )

    if address_info is None:
        raise ProviderError(
            f"Could not get address information from address {creator_address}!"
        )

    if "stake_address" not in address_info:
        # If a proposer doesn't have a stake address

        return {
            "valid": False,
            "message": f"Proposal creator {creator_address} does not have stake address",
        }

    creator_address = address_info["stake_address"]
    proposal.creator_stake_address = address_info["stake_address"]

    tx_info = cache.get_or_set(
        "tx_info",
        lambda: chain_provider.get_transaction_info(tx_hash),
        timeout,
        tx_hash,
    )

    if tx_info is None:
        raise ProviderError(f"Could not get transaction info from tx_hash {tx_hash}!")

    if not "block_time" in tx_info:
        raise ProviderError(
            "Chain provider returned value different from expected while trying to get current block_time!"
        )

    # Make sure user paid fees
    value_paid = cache.get_or_set(
        "value_paid",
        lambda: chain_provider.get_lovelace_sent(tx_hash, PLATFORM_ADDRESS),
        timeout,
        tx_hash,
    )

    if value_paid is None:
        raise ValueError(
            "Could not get lovelace paid to platform with tx hash {tx_hash} and platform address {PLATFORM_ADDRESS}"
        )

    if config_utils.get_config_value("require_fees") == True:
        fees = config_utils.get_fees(proposal.ballot_type)
        if value_paid < fees:
            return {
                "valid": False,
                "message": f"User did not pay enough fees! Expected {fees} and got {value_paid}",
            }

    proposal.status = "on-chain"
    proposal.tx_hash = tx_hash
    proposal.proposal_metadata = json.dumps(metadata)
    proposal.processed_date = func.now()
    proposal.onchain_date = datetime.datetime.utcfromtimestamp(
        int(tx_info["block_time"])
    )

    if overwrite_case:
        return {"valid": True, "details": "Overwriting proposal", "proposal": proposal}

    return {"valid": True, "proposal": proposal}


def validate_vote(
    vote: Vote | None,
    metadata: dict,
    tx_hash: str,
    chain_provider: Any,
    overwrite: bool,
) -> dict:

    overwrite_case = vote is not None and (
        vote.status == "on-chain" or vote.status == "invalid"
    )

    if vote is not None and metadata["VoteId"] != vote.vote_identifier:
        raise ValueError(
            f"Vote being overwritten {vote.vote_identifier} has different vote id from new one {metadata['VoteId']}!"
        )

    if overwrite_case and overwrite is False:
        logging.warning(
            f"Tried to overwrite vote {vote.vote_identifier} but failed because overwrite = False!"
        )

        return {
            "valid": False,
            "message": f"Tried to overwrite vote with overwrite = False! Proposal {vote.vote_identifier} already exists!",
        }

    proposal_identifier = metadata["ProposalId"]

    proposal: Proposal | None = Proposal.query.filter(
        Proposal.proposal_identifier == proposal_identifier
    ).first()

    if proposal is None:
        return {
            "valid": False,
            "message": f"Proposal {proposal_identifier} does not exist!",
        }

    if proposal.status != "on-chain":
        return {
            "valid": False,
            "message": f"Tried to process vote with proposal {proposal.proposal_identifier} that is not on-chain yet!",
        }

    if overwrite_case or vote is None:
        if overwrite_case:
            vote.source = "overwrite"
        else:
            vote = Vote()
            vote.source = "manual"

        vote.vote_identifier = metadata["VoteId"]
        vote.version = metadata["ObjectVersion"]
        vote.proposal = proposal

        vote_choices = []
        for meta_choice in metadata["Choices"]:
            question_identifier = meta_choice["QuestionId"]
            choice_identifier = meta_choice["ChoiceId"]

            choice: Choice | None = Choice.query.filter(
                Choice.choice_identifier == choice_identifier
            ).first()

            if choice is None:
                return {
                    "valid": False,
                    "message": f"Choice with choice id {choice_identifier} not found!",
                }

            # Make sure choice has right question and proposal IDs
            if not choice.question.question_identifier == question_identifier:
                return {
                    "valid": False,
                    "message": f"Question ID on database {choice.question.question_identifier} is different from metadata {question_identifier}!",
                }

            if not choice.question.proposal.proposal_identifier == proposal_identifier:
                return {
                    "valid": False,
                    "message": f"Proposal ID on database {choice.question.proposal.proposal_identifier} is different from metadata {proposal_identifier}!",
                }

            vote_choice = VoteChoice()
            vote_choice.choice = choice

            vote_choices.append(vote_choice)

        vote.vote_choices = vote_choices
        vote.version = metadata["ObjectVersion"]
        vote.source = "manual"

    # Caching timeout
    timeout = 1 * 60

    # Operations that apply to both cases (manual / front-end)

    tx_info = cache.get_or_set(
        "tx_info",
        lambda: chain_provider.get_transaction_info(tx_hash),
        timeout,
        tx_hash,
    )

    if tx_info is None:
        raise ProviderError(
            f"Chain provider failed while trying to get transaction {tx_hash} information!"
        )
    elif not "block_time" in tx_info:
        raise ProviderError(
            f"Chain provider returned value different from expected while trying to get transaction {tx_hash} info!"
        )

    block_time = int(tx_info["block_time"])

    if block_time < blockchain_utils.get_epoch_start_date(proposal.start_epoch):
        return {
            "valid": False,
            "message": f"Vote submitted before start epoch {proposal.start_epoch}!",
        }

    if block_time > blockchain_utils.get_epoch_end_date(proposal.end_epoch):
        return {
            "valid": False,
            "message": f"Vote submitted after end epoch {proposal.end_epoch}!",
        }

    voter_address = cache.get_or_set(
        "voter_address",
        lambda: chain_provider.get_sender_address(tx_hash),
        timeout,
        tx_hash,
    )

    if voter_address is None:
        raise ProviderError(f"Could not get sender address from tx_hash {tx_hash}!")

    address_info = cache.get_or_set(
        "address_info",
        lambda: chain_provider.get_address_info(voter_address),
        timeout,
        tx_hash,
    )

    if address_info is None:
        raise ProviderError(
            f"Could not get address information from address {voter_address}!"
        )

    if "stake_address" not in address_info:
        return {
            "valid": False,
            "message": f"Voter {voter_address} does not have stake address",
        }

    voter_address = address_info["stake_address"]
    vote.voter_stake_address = address_info["stake_address"]

    vote.status = "on-chain"
    vote.tx_hash = tx_hash
    vote.vote_metadata = json.dumps(metadata)
    vote.processed_date = func.now()
    vote.onchain_date = datetime.datetime.utcfromtimestamp(block_time)

    if overwrite_case:
        return {"valid": True, "details": "Overwriting vote", "vote": vote}

    return {"valid": True, "vote": vote}

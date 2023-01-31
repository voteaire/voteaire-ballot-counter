from __future__ import annotations

import datetime
import os

from model.vote import Vote
from model.proposal import Proposal

from dotenv import load_dotenv

load_dotenv()

LABEL = os.environ.get("LABEL")


def parse_long_string(string: str, sep=64) -> list:
    parsed = []

    for i in range(0, len(string), sep):
        parsed.append(string[i : i + sep])

    return parsed


def parse_string_list(lst: list) -> str:
    return "".join(lst)


def get_proposal_metadata(proposal):
    ballot_type = {}
    if proposal.ballot_type == "Simple":
        ballot_type = {"Name": "Simple"}
    elif proposal.ballot_type == "Delegated":
        ballot_type = {"Name": "Delegated", "PoolId": proposal.pool_id}
    elif proposal.ballot_type == "PolicyId":
        ballot_type = {"Name": "PolicyId", "PolicyId": [proposal.policy_id]}
    else:
        raise Exception(f"Non-existent type {proposal.ballot_type}")

    metadata_questions = []
    for question in proposal.questions:
        metadata_question = {}
        metadata_question["QuestionId"] = question.question_identifier
        metadata_question["Question"] = parse_long_string(question.question)

        if question.description is not None:
            metadata_question["Description"] = parse_long_string(question.description)

        metadata_question["ChoiceLimit"] = question.choice_limit

        metadata_choices = []
        for choice in question.choices:
            metadata_choice = {}

            metadata_choice["ChoiceId"] = choice.choice_identifier
            metadata_choice["Name"] = choice.choice

            if choice.description is not None:
                metadata_choice["Description"] = parse_long_string(choice.description)

            metadata_choices.append(metadata_choice)

        metadata_question["Choices"] = metadata_choices

        metadata_questions.append(metadata_question)

    metadata_content = {
        "ObjectType": "BallotProposal",
        "ObjectVersion": proposal.version,
        "NetworkId": proposal.network_id,
        "ProposalId": proposal.proposal_identifier,
        "ProposalURL": proposal.proposal_url,
        "BallotType": ballot_type,
        "Title": proposal.title,
        "Description": parse_long_string(proposal.description)
        if proposal.description
        else None,
        "Questions": metadata_questions,
        "VoteStartEpoch": proposal.start_epoch,
        "VoteEndEpoch": proposal.end_epoch,
        "SnapshotEpoch": proposal.snapshot_epoch,
    }

    if proposal.proposal_url is None:
        del metadata_content["ProposalURL"]

    if proposal.description is None:
        del metadata_content["Description"]

    return metadata_content


def get_vote_metadata(vote: Vote):
    return {
        "ObjectType": "VoteBallot",
        "ObjectVersion": vote.version,
        "VoteId": vote.vote_identifier,
        "ProposalId": vote.proposal.proposal_identifier,
        "Choices": [
            {
                "QuestionId": vote_choice.choice.question.question_identifier,
                "ChoiceId": vote_choice.choice.choice_identifier,
            }
            for vote_choice in vote.vote_choices
        ],
    }

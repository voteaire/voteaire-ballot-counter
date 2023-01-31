from __future__ import annotations

import json
import copy
import sys

import test_utils

from unit.api.fixtures import api


def test_counter(api, mocker):
    _, app = api

    sys.path.append("src")

    from meta.vote_counter import VoteCounter
    from meta.chain_providers import mock

    from model import db
    from model.proposal import Proposal
    from model.question import Question
    from model.choice import Choice

    import lib.metadata_utils as utils

    with app.app_context():
        proposal: Proposal = test_utils.fake_proposal(db.session)

        proposal_metadata = json.loads(proposal.proposal_metadata)

        questions = proposal.questions
        choices = [question.choices for question in questions]

    counter = VoteCounter()
    vote_metadata = {
        "ObjectType": "VoteBallot",
        "ObjectVersion": "1.0.0",
        "VoteId": "83c7d4cb-2eb9-469a-911f-8a424acecebe",
        "ProposalId": proposal.proposal_identifier,
        "Choices": [
            {
                "QuestionId": questions[0].question_identifier,
                "ChoiceId": choices[0][1].choice_identifier,
            },
            {
                "QuestionId": questions[1].question_identifier,
                "ChoiceId": choices[1][0].choice_identifier,
            },
            {
                "QuestionId": questions[1].question_identifier,
                "ChoiceId": choices[1][1].choice_identifier,
            },
        ],
    }

    expected_results = [
        {
            "question_id": questions[0].question_identifier,
            "question_name": questions[0].question,
            "responses": [
                {
                    "choice_id": choices[0][1].choice_identifier,
                    "choice_name": choices[0][1].choice,
                }
            ],
        },
        {
            "question_id": questions[1].question_identifier,
            "question_name": questions[1].question,
            "responses": [
                {
                    "choice_id": choices[1][0].choice_identifier,
                    "choice_name": choices[1][0].choice,
                },
                {
                    "choice_id": choices[1][1].choice_identifier,
                    "choice_name": choices[1][1].choice,
                },
            ],
        },
    ]

    assert counter.process_vote(vote_metadata, proposal_metadata) == {
        "status": True,
        "results": expected_results,
    }

    # Wrong ObjectType
    temp_vote_metadata = copy.deepcopy(vote_metadata)
    temp_vote_metadata["ObjectType"] = "BallotPropsal"

    assert (
        counter.process_vote(temp_vote_metadata, proposal_metadata)["status"] == False
    )

    # Wrong version
    temp_vote_metadata = copy.deepcopy(vote_metadata)
    temp_vote_metadata["ObjectVersion"] = "2.0.0"

    assert (
        counter.process_vote(temp_vote_metadata, proposal_metadata)["status"] == False
    )

    # Wrong proposal ID
    temp_vote_metadata = copy.deepcopy(vote_metadata)
    temp_vote_metadata["ProposalId"] = "f4da7817-2ffd-456c-98fd-9a78d645f482"

    assert (
        counter.process_vote(temp_vote_metadata, proposal_metadata)["status"] == False
    )

    # Not respecting choice limit
    temp_vote_metadata = copy.deepcopy(vote_metadata)

    temp_vote_metadata["Choices"].append(
        {
            "QuestionId": questions[0].question_identifier,
            "ChoiceId": choices[0][1].choice_identifier,
        }
    )

    assert (
        counter.process_vote(temp_vote_metadata, proposal_metadata)["status"] == False
    )

    # No proposal snapshot
    proposal.snapshot_epoch = None

    temp_proposal = copy.deepcopy(proposal)
    temp_proposal_metadata = utils.get_proposal_metadata(temp_proposal)

    assert (
        counter.process_vote(vote_metadata, temp_proposal_metadata)["status"] == False
    )

    # Using policy ID
    proposal_metadata["BallotType"] = {"Name": "PolicyId", "PolicyId": "<policy>"}

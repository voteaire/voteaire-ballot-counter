import datetime
import json
import sys

from test_utils.safe_add import safe_add


def fake_proposal(session, add_to_db=True, **args):
    sys.path.append("src")

    from model.proposal import Proposal
    from model.question import Question
    from model.choice import Choice

    from lib import metadata_utils

    question_1 = Question()
    question_1.question = "question_1"
    question_1.choice_limit = 1
    question_1.description = "description_1"

    choice_11 = Choice()
    choice_11.choice = "choice_11"
    choice_11.description = "choice_description_11"

    choice_12 = Choice()
    choice_12.choice = "choice_12"
    choice_12.description = "choice_description_12"

    question_1.choices = [choice_11, choice_12]

    question_2 = Question()
    question_2.question = "question_2"
    question_2.choice_limit = 2
    question_2.description = "description_2"

    choice_21 = Choice()
    choice_21.choice = "choice_21"
    choice_21.description = "choice_description_21"

    choice_22 = Choice()
    choice_22.choice = "choice_22"
    choice_22.description = "choice_description_22"

    question_2.choices = [choice_21, choice_22]

    questions = [question_1, question_2]

    proposal = Proposal()
    proposal.version = "1.0.0"
    proposal.network_id = "network_id"
    proposal.proposal_url = "https://example.com"

    if "id" in args:
        proposal.id = args["id"]

    if "proposal_identifier" in args:
        proposal.proposal_identifier = args["proposal_identifier"]

    if "title" in args:
        proposal.title = args["title"]
    else:
        proposal.title = "test_get_proposal"

    if "creator_stake_address" in args:
        proposal.creator_stake_address = args["creator_stake_address"]
    else:
        proposal.creator_stake_address = "stake_test123"

    if "ballot_type" in args:
        proposal.ballot_type = args["ballot_type"]
    else:
        proposal.ballot_type = "Simple"

    if "pool_id" in args:
        proposal.pool_id = args["pool_id"]
    else:
        proposal.pool_id = None

    if "policy_id" in args:
        proposal.policy_id = args["policy_id"]
    else:
        proposal.policy_id = None

    if "snapshot_epoch" in args:
        proposal.snapshot_epoch = args["snapshot_epoch"]
    else:
        proposal.snapshot_epoch = 180

    if "tx_hash" in args:
        proposal.tx_hash = args["tx_hash"]
    else:
        proposal.tx_hash = "<hash>"

    if "status" in args:
        proposal.status = args["status"]
    else:
        proposal.status = "on-chain"

    if "start_epoch" in args:
        proposal.start_epoch = args["start_epoch"]
    else:
        proposal.start_epoch = 200

    if "end_epoch" in args:
        proposal.end_epoch = args["end_epoch"]
    else:
        proposal.end_epoch = 201

    proposal.questions = questions

    if "creation_date" in args:
        proposal.creation_date = args["creation_date"]
    else:
        proposal.creation_date = datetime.datetime.strptime(
            "2042-03-28 02:00:00", "%Y-%m-%d %H:%M:%S"
        )

    if "processed_date" in args:
        proposal.processed_date = args["processed_date"]

    if "onchain_date" in args:
        proposal.onchain_date = args["onchain_date"]

    session.add(proposal)
    session.flush()

    if "proposal_metadata" in args:
        proposal.proposal_metadata = args["proposal_metadata"]
    else:
        proposal.proposal_metadata = json.dumps(
            metadata_utils.get_proposal_metadata(proposal)
        )

    if add_to_db:
        safe_add(session, proposal)
    else:
        session.rollback()

    return proposal

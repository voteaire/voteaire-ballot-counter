import sys
import test_utils


def fake_vote(session, add_to_db=True, **args):
    sys.path.append("src")

    from model.vote import Vote
    from model.vote_choice import VoteChoice

    proposal = (
        test_utils.fake_proposal(
            session,
            add_to_db=True,
            source="front-end",
            status="on-chain",
            start_epoch=200,
            end_epoch=201,
            tx_hash="HASH1",
        )
        if "proposal" not in args
        else args["proposal"]
    )

    choice = proposal.questions[0].choices[0]

    vote = Vote()
    vote.proposal = proposal
    # vote.status = args["status"] if "status" in args else "draft"

    if "vote_choices" in args:
        vote.vote_choices = args["vote_choices"]
    else:
        vote_choice = VoteChoice()
        vote_choice.choice = choice

        vote.vote_choices = [vote_choice]

    vote.version = "1.0.0" if not "version" in args else args["version"]
    vote.voter_stake_address = (
        "stake_test456"
        if not "voter_stake_address" in args
        else args["voter_stake_address"]
    )

    # vote.status = args["status"] if "status" in args else "draft"

    if add_to_db:
        test_utils.safe_add(session, vote)
    else:
        session.rollback()

    return vote

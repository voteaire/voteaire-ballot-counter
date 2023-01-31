import sys
import test_utils
import datetime

from integration.fixtures import weight_worker


def test_weight_worker(weight_worker):
    session = weight_worker

    sys.path.append("src")

    from model.proposal import Proposal
    from model.question import Question
    from model.choice import Choice

    from model.vote import Vote
    from model.vote_choice import VoteChoice

    from lib import metadata_utils

    proposal = test_utils.fake_proposal(session, snapshot_epoch=180)

    choice = proposal.questions[0].choices[0]

    # Simple valid vote
    vote = Vote()
    vote.proposal = proposal

    vote_choice = VoteChoice()
    vote_choice.choice = choice

    vote.vote_choices = [vote_choice]
    vote.version = "1.0.0"
    vote.status = "on-chain"
    vote.voter_stake_address = (
        "stake_test1uqmua3stfp60dlwkxfh8jk7d49tu9u2de9q0vul9mdcgd6gasp4mx"
    )

    test_utils.safe_add(session, vote)

    worker_max_delay = 5
    start_time = datetime.datetime.now()

    while True:
        session.refresh(vote)

        assert proposal is not None
        assert vote is not None

        if vote.weight is not None:
            assert vote.weight == 99238983438990
            break

        assert datetime.datetime.now() < start_time + datetime.timedelta(
            seconds=worker_max_delay
        )

    # Duplicate vote
    vote = Vote()
    vote.proposal = proposal

    vote_choice = VoteChoice()
    vote_choice.choice = choice

    vote.vote_choices = [vote_choice]
    vote.version = "1.0.0"
    vote.status = "on-chain"
    vote.voter_stake_address = (
        "stake_test1uqmua3stfp60dlwkxfh8jk7d49tu9u2de9q0vul9mdcgd6gasp4mx"
    )

    test_utils.safe_add(session, vote)

    worker_max_delay = 5
    start_time = datetime.datetime.now()

    while True:
        session.refresh(vote)

        assert vote is not None

        if vote.weight is not None:
            assert vote.weight == 0
            assert vote.error_message is not None
            break

        assert datetime.datetime.now() < start_time + datetime.timedelta(
            seconds=worker_max_delay
        )

    # Voter without delegation history
    vote = Vote()
    vote.proposal = proposal

    vote_choice = VoteChoice()
    vote_choice.choice = choice

    vote.vote_choices = [vote_choice]
    vote.version = "1.0.0"
    vote.status = "on-chain"
    vote.voter_stake_address = (
        "stake_test1uqselr3llm7gyw2a7zlule89wmu0sf96urrnr034xgwqr4csd30df"
    )

    test_utils.safe_add(session, vote)

    worker_max_delay = 5
    start_time = datetime.datetime.now()

    while True:
        session.refresh(vote)

        assert vote is not None

        if vote.weight is not None:
            assert vote.weight == 0
            assert vote.error_message is not None
            break

        assert datetime.datetime.now() < start_time + datetime.timedelta(
            seconds=worker_max_delay
        )

    # Delegate vote (success)
    proposal = test_utils.fake_proposal(
        session,
        snapshot_epoch=180,
        ballot_type="Delegated",
        pool_id="pool1y823jseas7d7czqmvqwseyaqjqrgrwvlrhlgfcuqjv7xjmdvd50",
    )

    vote = Vote()
    vote.proposal = proposal

    vote_choice = VoteChoice()
    vote_choice.choice = choice

    vote.vote_choices = [vote_choice]
    vote.version = "1.0.0"
    vote.status = "on-chain"
    vote.voter_stake_address = (
        "stake_test1uqmua3stfp60dlwkxfh8jk7d49tu9u2de9q0vul9mdcgd6gasp4mx"
    )

    test_utils.safe_add(session, vote)

    worker_max_delay = 5
    start_time = datetime.datetime.now()

    while True:
        session.refresh(vote)

        assert vote is not None

        if vote.weight is not None:
            assert vote.weight == 99_238_983_438_990
            assert vote.error_message is None
            break

        assert datetime.datetime.now() < start_time + datetime.timedelta(
            seconds=worker_max_delay
        )

    # Delegate vote (failure)
    vote = Vote()
    vote.proposal = proposal

    vote_choice = VoteChoice()
    vote_choice.choice = choice

    vote.vote_choices = [vote_choice]
    vote.version = "1.0.0"
    vote.status = "on-chain"
    vote.voter_stake_address = (
        "stake_test1uz6pf4cruzggqytel5f7z8sa0ne7lctp005hazjpv6f9mwcz5uj6c"
    )

    test_utils.safe_add(session, vote)

    worker_max_delay = 5
    start_time = datetime.datetime.now()

    while True:
        session.refresh(vote)

        assert vote is not None

        if vote.weight is not None:
            assert vote.weight == 0
            assert vote.error_message is not None
            break

        assert datetime.datetime.now() < start_time + datetime.timedelta(
            seconds=worker_max_delay
        )

    # Snapshot in the future (worker should do nothing until our current epoch becomes 450)
    proposal = test_utils.fake_proposal(
        session,
        snapshot_epoch=450,
    )

    vote = Vote()
    vote.proposal = proposal

    vote_choice = VoteChoice()
    vote_choice.choice = choice

    vote.vote_choices = [vote_choice]
    vote.version = "1.0.0"
    vote.status = "on-chain"
    vote.voter_stake_address = (
        "stake_test1uqmua3stfp60dlwkxfh8jk7d49tu9u2de9q0vul9mdcgd6gasp4mx"
    )

    test_utils.safe_add(session, vote)

    worker_max_delay = 5
    start_time = datetime.datetime.now()

    while True:
        session.refresh(vote)

        assert vote is not None
        assert vote.weight is None

        if datetime.datetime.now() > start_time + datetime.timedelta(
            seconds=worker_max_delay
        ):
            print(
                datetime.datetime.now(),
                start_time + datetime.timedelta(seconds=worker_max_delay),
            )

            break

    # PolicyId votes
    proposal = test_utils.fake_proposal(
        session,
        snapshot_epoch=200,
        ballot_type="PolicyId",
        policy_id="10ed5520cb21ce3ca6e552f8e63a9deb1390cc2d47b522db4c392006",
    )

    vote = Vote()
    vote.proposal = proposal

    vote_choice = VoteChoice()
    vote_choice.choice = choice

    vote.vote_choices = [vote_choice]
    vote.version = "1.0.0"
    vote.status = "on-chain"
    vote.voter_stake_address = (
        "stake_test1uqselr3llm7gyw2a7zlule89wmu0sf96urrnr034xgwqr4csd30df"
    )

    test_utils.safe_add(session, vote)

    worker_max_delay = 5
    start_time = datetime.datetime.now()

    while True:
        session.refresh(vote)

        assert vote is not None

        if vote.weight is not None:
            assert vote.weight == 11
            assert vote.error_message is None
            break

        assert datetime.datetime.now() < start_time + datetime.timedelta(
            seconds=worker_max_delay
        )

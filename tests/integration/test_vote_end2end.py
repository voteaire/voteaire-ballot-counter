"""End to End Integration test, we expect everything to go well,
as long as the following assumptions hold true:

* Application is running in the background (docker compose up will do it) with snapshotter
* There are three keys inside the integrations/keys folder (alice, bob, platform)
with payment.skey and stake.skey files
* Keys have a reasonable amount of ADA for fees (ideally > 100 ADA)
"""

import os
import sys
import json
import requests
import uuid
import dotenv
import datetime

from pycardano import *
from time import sleep
from integration.fixtures import session
from test_utils import fake_proposal

dotenv.load_dotenv("tests/.env")

PROJECT_ID = os.getenv("BLOCKFROST_PROJECT_ID")
if PROJECT_ID is None:
    raise ValueError("PROJECT_ID undefined")

API_ENDPOINT = os.getenv("API_ENDPOINT")
if API_ENDPOINT is None:
    raise ValueError("API_ENDPOINT undefined")

NETWORK = Network.TESTNET

with open("tests/integration/keys/platform/payment.addr", "r") as addr:
    PLATFORM_ADDRESS = addr.read()


def load_user(user: str) -> dict:
    psk = PaymentSigningKey.load(f"tests/integration/keys/{user}/payment.skey")
    ssk = StakeSigningKey.load(f"tests/integration/keys/{user}/stake.skey")

    pvk = PaymentVerificationKey.from_signing_key(psk)
    svk = StakeVerificationKey.from_signing_key(ssk)

    # Derive an address from payment verification key and stake verification key
    address = Address(pvk.hash(), svk.hash(), NETWORK)

    return {
        "payment_skey": psk,
        "stake_skey": ssk,
        "payment_vkey": pvk,
        "stake_vkey": svk,
        "address": address.encode(),
        "stake_address": Address(staking_part=svk.hash(), network=NETWORK).encode(),
    }


def create_proposal(creator: str, metadata: dict, fees: int, platform_addr: str):
    # Read keys to memory
    # Assume there is a payment.skey file sitting in current directory
    psk = PaymentSigningKey.load(f"tests/integration/keys/{creator}/payment.skey")
    # Assume there is a stake.skey file sitting in current directory
    ssk = StakeSigningKey.load(f"tests/integration/keys/{creator}/stake.skey")

    pvk = PaymentVerificationKey.from_signing_key(psk)
    svk = StakeVerificationKey.from_signing_key(ssk)

    # Derive an address from payment verification key and stake verification key
    creator_addr = Address(pvk.hash(), svk.hash(), NETWORK)

    # Create a BlockFrost chain context
    context = BlockFrostChainContext(PROJECT_ID, NETWORK)

    # Create a transaction builder
    builder = TransactionBuilder(context)

    # Tell the builder that transaction input will come from a specific address, assuming that there are some ADA and native
    # assets sitting at this address. "add_input_address" could be called multiple times with different address.
    builder.add_input_address(creator_addr)

    # Send 1.5 ADA and a native asset (CHOC) in quantity of 2000 to an address.
    builder.add_output(
        TransactionOutput(
            Address.from_primitive(platform_addr),
            Value.from_primitive([fees]),
        )
    )

    auxiliary_data = AuxiliaryData(AlonzoMetadata(metadata=Metadata(metadata)))
    builder.auxiliary_data = auxiliary_data

    # Create final signed transaction
    signed_tx = builder.build_and_sign([psk], change_address=creator_addr)

    # Submit signed transaction to the NETWORK
    context.submit_tx(signed_tx.to_cbor())

    return str(signed_tx.id)


def create_vote(creator: str, metadata: dict):
    # Read keys to memory
    # Assume there is a payment.skey file sitting in current directory
    psk = PaymentSigningKey.load(f"tests/integration/keys/{creator}/payment.skey")
    # Assume there is a stake.skey file sitting in current directory
    ssk = StakeSigningKey.load(f"tests/integration/keys/{creator}/stake.skey")

    pvk = PaymentVerificationKey.from_signing_key(psk)
    svk = StakeVerificationKey.from_signing_key(ssk)

    # Derive an address from payment verification key and stake verification key
    voter_addr = Address(pvk.hash(), svk.hash(), NETWORK)

    # Create a BlockFrost chain context
    context = BlockFrostChainContext(PROJECT_ID, NETWORK)

    # Create a transaction builder
    builder = TransactionBuilder(context)

    # Tell the builder that transaction input will come from a specific address, assuming that there are some ADA and native
    # assets sitting at this address. "add_input_address" could be called multiple times with different address.
    builder.add_input_address(voter_addr)

    builder.add_output(
        TransactionOutput(
            voter_addr,
            Value.from_primitive([utils.min_lovelace(Value(0), context)]),
        )
    )

    auxiliary_data = AuxiliaryData(AlonzoMetadata(metadata=Metadata(metadata)))
    builder.auxiliary_data = auxiliary_data

    # Create final signed transaction
    signed_tx = builder.build_and_sign([psk], change_address=voter_addr)

    # Submit signed transaction to the NETWORK
    context.submit_tx(signed_tx.to_cbor())

    return str(signed_tx.id)


def test_success_vote(session):
    sys.path.append("src")

    from model.processed_log import ProcessedLog
    from model.proposal import Proposal
    from model.vote import Vote

    creator = "alice"
    voter = "bob"
    lovelace_fee = 2_000_000

    proposal_metadata = {
        1916: {
            "Title": "Friends Trivia",
            "NetworkId": "Voteaire - Testing",
            "Questions": [
                {
                    "Choices": [
                        {
                            "Name": "Accountant",
                            "ChoiceId": str(uuid.uuid4()),
                        },
                        {
                            "Name": "Statistical Analysis",
                            "ChoiceId": str(uuid.uuid4()),
                        },
                        {
                            "Name": "Graphic Designer",
                            "ChoiceId": str(uuid.uuid4()),
                        },
                    ],
                    "Question": ["What was Chandler's job?"],
                    "QuestionId": str(uuid.uuid4()),
                    "ChoiceLimit": 1,
                },
                {
                    "Choices": [
                        {
                            "Name": "Alice",
                            "ChoiceId": str(uuid.uuid4()),
                        },
                        {
                            "Name": "Erika",
                            "ChoiceId": str(uuid.uuid4()),
                        },
                        {
                            "Name": "Ursula",
                            "ChoiceId": str(uuid.uuid4()),
                        },
                    ],
                    "Question": ["What was the name of Phoeby's twin sister?"],
                    "QuestionId": str(uuid.uuid4()),
                    "ChoiceLimit": 2,
                    "Description": ["Sample description"],
                },
            ],
            "BallotType": {"Name": "Simple"},
            "ObjectType": "BallotProposal",
            "ProposalId": str(uuid.uuid4()),
            "VoteEndEpoch": 202,
            "ObjectVersion": "1.0.0",
            "SnapshotEpoch": 200,
            "VoteStartEpoch": 201,
        }
    }

    tx_hash = create_proposal(
        creator, proposal_metadata, lovelace_fee, PLATFORM_ADDRESS
    )

    print(f"Successfully submitted proposal {tx_hash}")

    timeout = 4 * 60 + 20  # Max delay for the transaction to get on-chain
    start_time = datetime.datetime.now()

    while True:
        process = ProcessedLog.query.filter(ProcessedLog.tx_hash == tx_hash).first()

        if process is not None:
            print("Finally! Found a matching process!")

            assert process.success == True
            assert process.valid == True
            assert process.tx_metadata == proposal_metadata[1916]

            proposal = Proposal.query.filter(Proposal.id == process.proposal_id).first()
            assert proposal is not None
            assert proposal.status == "on-chain"

            break

        current_time = datetime.datetime.now()

        assert (
            start_time + datetime.timedelta(seconds=timeout) >= current_time
        ), "timeout expired"

        sleep(5)

    vote_metadata = {
        1916: {
            "ObjectType": "VoteBallot",
            "ObjectVersion": "1.0.0",
            "VoteId": str(uuid.uuid4()),
            "ProposalId": proposal_metadata[1916]["ProposalId"],
            "Choices": [
                {
                    "QuestionId": proposal_metadata[1916]["Questions"][0]["QuestionId"],
                    "ChoiceId": proposal_metadata[1916]["Questions"][0]["Choices"][1][
                        "ChoiceId"
                    ],
                },
                {
                    "QuestionId": proposal_metadata[1916]["Questions"][1]["QuestionId"],
                    "ChoiceId": proposal_metadata[1916]["Questions"][1]["Choices"][0][
                        "ChoiceId"
                    ],
                },
                {
                    "QuestionId": proposal_metadata[1916]["Questions"][1]["QuestionId"],
                    "ChoiceId": proposal_metadata[1916]["Questions"][1]["Choices"][2][
                        "ChoiceId"
                    ],
                },
            ],
        }
    }

    tx_hash = create_vote("bob", vote_metadata)

    timeout = 4 * 60 + 20  # Max delay for the transaction to get on-chain
    start_time = datetime.datetime.now()

    while True:
        process = ProcessedLog.query.filter(ProcessedLog.tx_hash == tx_hash).first()

        if process is not None:
            print("Finally! Found a matching process!")

            assert process.success == True
            assert process.valid == True
            assert process.tx_metadata == vote_metadata[1916]

            vote = Vote.query.filter(Vote.id == process.vote_id).first()
            assert vote is not None
            assert vote.status == "on-chain"

            break

        current_time = datetime.datetime.now()

        assert (
            start_time + datetime.timedelta(seconds=timeout) >= current_time
        ), "timeout expired"

        sleep(5)
    print(tx_hash)


def test_wrong_schema_vote(session):
    sys.path.append("src")

    from model.processed_log import ProcessedLog
    from model.proposal import Proposal
    from model.vote import Vote

    creator = "alice"
    voter = "bob"
    lovelace_fee = 2_000_000

    proposal_metadata = {
        1916: {
            "Title": "Friends Trivia",
            "NetworkId": "Voteaire - Testing",
            "Questions": [
                {
                    "Choices": [
                        {
                            "Name": "Accountant",
                            "ChoiceId": str(uuid.uuid4()),
                        },
                        {
                            "Name": "Statistical Analysis",
                            "ChoiceId": str(uuid.uuid4()),
                        },
                        {
                            "Name": "Graphic Designer",
                            "ChoiceId": str(uuid.uuid4()),
                        },
                    ],
                    "Question": ["What was Chandler's job?"],
                    "QuestionId": str(uuid.uuid4()),
                    "ChoiceLimit": 1,
                },
                {
                    "Choices": [
                        {
                            "Name": "Alice",
                            "ChoiceId": str(uuid.uuid4()),
                        },
                        {
                            "Name": "Erika",
                            "ChoiceId": str(uuid.uuid4()),
                        },
                        {
                            "Name": "Ursula",
                            "ChoiceId": str(uuid.uuid4()),
                        },
                    ],
                    "Question": ["What was the name of Phoeby's twin sister?"],
                    "QuestionId": str(uuid.uuid4()),
                    "ChoiceLimit": 2,
                    "Description": ["Sample description"],
                },
            ],
            "BallotType": {"Name": "Simple"},
            "ObjectType": "BallotProposal",
            "ProposalId": str(uuid.uuid4()),
            "VoteEndEpoch": 202,
            "ObjectVersion": "1.0.0",
            "SnapshotEpoch": 200,
            "VoteStartEpoch": 201,
        }
    }

    tx_hash = create_proposal(
        creator, proposal_metadata, lovelace_fee, PLATFORM_ADDRESS
    )

    print(f"Successfully submitted proposal {tx_hash}")

    timeout = 4 * 60 + 20  # Max delay for the transaction to get on-chain
    start_time = datetime.datetime.now()

    while True:
        process = ProcessedLog.query.filter(ProcessedLog.tx_hash == tx_hash).first()

        if process is not None:
            print("Finally! Found a matching process!")

            assert process.success == True
            assert process.valid == True
            assert process.tx_metadata == proposal_metadata[1916]

            proposal = Proposal.query.filter(Proposal.id == process.proposal_id).first()
            assert proposal is not None
            assert proposal.status == "on-chain"

            break

        current_time = datetime.datetime.now()

        assert (
            start_time + datetime.timedelta(seconds=timeout) >= current_time
        ), "timeout expired"

        sleep(5)

    vote_metadata = {
        1916: {
            "ObjectType": "VoteBallot",
            "ObjectVersion": "7.7.7",
            "VoteId": str(uuid.uuid4()),
            "ProposalId": proposal_metadata[1916]["ProposalId"],
            "Choices": [
                {
                    "QuestionId": proposal_metadata[1916]["Questions"][0]["QuestionId"],
                    "ChoiceId": proposal_metadata[1916]["Questions"][0]["Choices"][1][
                        "ChoiceId"
                    ],
                },
                {
                    "QuestionId": proposal_metadata[1916]["Questions"][1]["QuestionId"],
                    "ChoiceId": proposal_metadata[1916]["Questions"][1]["Choices"][0][
                        "ChoiceId"
                    ],
                },
                {
                    "QuestionId": proposal_metadata[1916]["Questions"][1]["QuestionId"],
                    "ChoiceId": proposal_metadata[1916]["Questions"][1]["Choices"][2][
                        "ChoiceId"
                    ],
                },
            ],
        }
    }

    tx_hash = create_vote("bob", vote_metadata)

    timeout = 4 * 60 + 20  # Max delay for the transaction to get on-chain
    start_time = datetime.datetime.now()

    while True:
        process = ProcessedLog.query.filter(ProcessedLog.tx_hash == tx_hash).first()

        if process is not None:
            print("Finally! Found a matching process!")

            assert process.success == True
            assert process.valid == False
            assert process.tx_metadata == vote_metadata[1916]

            vote = Vote.query.filter(Vote.id == process.vote_id).first()
            assert vote is None

            break

        current_time = datetime.datetime.now()

        assert (
            start_time + datetime.timedelta(seconds=timeout) >= current_time
        ), "timeout expired"

        sleep(5)
    print(tx_hash)


def test_repeated_vote(session):
    sys.path.append("src")

    from model.processed_log import ProcessedLog
    from model.proposal import Proposal
    from model.vote import Vote

    creator = "alice"
    voter = "bob"
    lovelace_fee = 2_000_000

    proposal_metadata = {
        1916: {
            "Title": "Friends Trivia",
            "NetworkId": "Voteaire - Testing",
            "Questions": [
                {
                    "Choices": [
                        {
                            "Name": "Accountant",
                            "ChoiceId": str(uuid.uuid4()),
                        },
                        {
                            "Name": "Statistical Analysis",
                            "ChoiceId": str(uuid.uuid4()),
                        },
                        {
                            "Name": "Graphic Designer",
                            "ChoiceId": str(uuid.uuid4()),
                        },
                    ],
                    "Question": ["What was Chandler's job?"],
                    "QuestionId": str(uuid.uuid4()),
                    "ChoiceLimit": 1,
                },
                {
                    "Choices": [
                        {
                            "Name": "Alice",
                            "ChoiceId": str(uuid.uuid4()),
                        },
                        {
                            "Name": "Erika",
                            "ChoiceId": str(uuid.uuid4()),
                        },
                        {
                            "Name": "Ursula",
                            "ChoiceId": str(uuid.uuid4()),
                        },
                    ],
                    "Question": ["What was the name of Phoeby's twin sister?"],
                    "QuestionId": str(uuid.uuid4()),
                    "ChoiceLimit": 2,
                    "Description": ["Sample description"],
                },
            ],
            "BallotType": {"Name": "Simple"},
            "ObjectType": "BallotProposal",
            "ProposalId": str(uuid.uuid4()),
            "VoteEndEpoch": 202,
            "ObjectVersion": "1.0.0",
            "SnapshotEpoch": 200,
            "VoteStartEpoch": 201,
        }
    }

    tx_hash = create_proposal(
        creator, proposal_metadata, lovelace_fee, PLATFORM_ADDRESS
    )

    print(f"Successfully submitted proposal {tx_hash}")

    timeout = 4 * 60 + 20  # Max delay for the transaction to get on-chain
    start_time = datetime.datetime.now()

    while True:
        process = ProcessedLog.query.filter(ProcessedLog.tx_hash == tx_hash).first()

        if process is not None:
            print("Finally! Found a matching process!")

            assert process.success == True
            assert process.valid == True
            assert process.tx_metadata == proposal_metadata[1916]

            proposal = Proposal.query.filter(Proposal.id == process.proposal_id).first()
            assert proposal is not None
            assert proposal.status == "on-chain"

            break

        current_time = datetime.datetime.now()

        assert (
            start_time + datetime.timedelta(seconds=timeout) >= current_time
        ), "timeout expired"

        sleep(5)

    vote_metadata = {
        1916: {
            "ObjectType": "VoteBallot",
            "ObjectVersion": "1.0.0",
            "VoteId": str(uuid.uuid4()),
            "ProposalId": proposal_metadata[1916]["ProposalId"],
            "Choices": [
                {
                    "QuestionId": proposal_metadata[1916]["Questions"][0]["QuestionId"],
                    "ChoiceId": proposal_metadata[1916]["Questions"][0]["Choices"][1][
                        "ChoiceId"
                    ],
                },
                {
                    "QuestionId": proposal_metadata[1916]["Questions"][1]["QuestionId"],
                    "ChoiceId": proposal_metadata[1916]["Questions"][1]["Choices"][0][
                        "ChoiceId"
                    ],
                },
                {
                    "QuestionId": proposal_metadata[1916]["Questions"][1]["QuestionId"],
                    "ChoiceId": proposal_metadata[1916]["Questions"][1]["Choices"][2][
                        "ChoiceId"
                    ],
                },
            ],
        }
    }

    tx_hash = create_vote("bob", vote_metadata)
    print(f"Successfully submitted vote {tx_hash}")

    timeout = 4 * 60 + 20  # Max delay for the transaction to get on-chain
    start_time = datetime.datetime.now()

    while True:
        process = ProcessedLog.query.filter(ProcessedLog.tx_hash == tx_hash).first()

        if process is not None:
            print("Finally! Found a matching process!")

            assert process.success == True
            assert process.valid == True
            assert process.tx_metadata == vote_metadata[1916]

            vote = Vote.query.filter(Vote.id == process.vote_id).first()
            assert vote is not None
            assert vote.id == process.vote_id

            break

        current_time = datetime.datetime.now()

        assert (
            start_time + datetime.timedelta(seconds=timeout) >= current_time
        ), "timeout expired"

        sleep(5)

    tx_hash = create_vote("bob", vote_metadata)
    print(f"Successfully submitted vote {tx_hash}")

    timeout = 4 * 60 + 20  # Max delay for the transaction to get on-chain
    start_time = datetime.datetime.now()

    while True:
        process = ProcessedLog.query.filter(ProcessedLog.tx_hash == tx_hash).first()

        if process is not None:
            print("Finally! Found a matching process!")

            assert process.success == True
            assert process.valid == False
            assert process.tx_metadata == vote_metadata[1916]

            vote = Vote.query.filter(Vote.id == process.vote_id).first()
            assert vote is None

            break

        current_time = datetime.datetime.now()

        assert (
            start_time + datetime.timedelta(seconds=timeout) >= current_time
        ), "timeout expired"

        sleep(5)


def test_inexistent_proposal_vote(session):
    sys.path.append("src")

    from model.processed_log import ProcessedLog
    from model.proposal import Proposal
    from model.vote import Vote

    timeout = 4 * 60 + 20  # Max delay for the transaction to get on-chain
    start_time = datetime.datetime.now()

    vote_metadata = {
        1916: {
            "ObjectType": "VoteBallot",
            "ObjectVersion": "1.0.0",
            "VoteId": str(uuid.uuid4()),
            "ProposalId": str(uuid.uuid4()),
            "Choices": [
                {
                    "QuestionId": str(uuid.uuid4()),
                    "ChoiceId": str(uuid.uuid4()),
                },
                {
                    "QuestionId": str(uuid.uuid4()),
                    "ChoiceId": str(uuid.uuid4()),
                },
                {
                    "QuestionId": str(uuid.uuid4()),
                    "ChoiceId": str(uuid.uuid4()),
                },
            ],
        }
    }

    tx_hash = create_vote("bob", vote_metadata)
    print(f"Successfully submitted vote {tx_hash}")

    timeout = 4 * 60 + 20  # Max delay for the transaction to get on-chain
    start_time = datetime.datetime.now()

    while True:
        process = ProcessedLog.query.filter(ProcessedLog.tx_hash == tx_hash).first()

        if process is not None:
            print("Finally! Found a matching process!")

            assert process.success == True
            assert process.valid == False
            assert process.tx_metadata == vote_metadata[1916]

            vote = Vote.query.filter(Vote.id == process.vote_id).first()
            assert vote is None

            break

        current_time = datetime.datetime.now()

        assert (
            start_time + datetime.timedelta(seconds=timeout) >= current_time
        ), "timeout expired"

        sleep(5)


def test_inexistent_question_vote(session):
    sys.path.append("src")

    from model.processed_log import ProcessedLog
    from model.proposal import Proposal
    from model.vote import Vote

    creator = "alice"
    voter = "bob"
    lovelace_fee = 2_000_000

    proposal_metadata = {
        1916: {
            "Title": "Friends Trivia",
            "NetworkId": "Voteaire - Testing",
            "Questions": [
                {
                    "Choices": [
                        {
                            "Name": "Accountant",
                            "ChoiceId": str(uuid.uuid4()),
                        },
                        {
                            "Name": "Statistical Analysis",
                            "ChoiceId": str(uuid.uuid4()),
                        },
                        {
                            "Name": "Graphic Designer",
                            "ChoiceId": str(uuid.uuid4()),
                        },
                    ],
                    "Question": ["What was Chandler's job?"],
                    "QuestionId": str(uuid.uuid4()),
                    "ChoiceLimit": 1,
                },
                {
                    "Choices": [
                        {
                            "Name": "Alice",
                            "ChoiceId": str(uuid.uuid4()),
                        },
                        {
                            "Name": "Erika",
                            "ChoiceId": str(uuid.uuid4()),
                        },
                        {
                            "Name": "Ursula",
                            "ChoiceId": str(uuid.uuid4()),
                        },
                    ],
                    "Question": ["What was the name of Phoeby's twin sister?"],
                    "QuestionId": str(uuid.uuid4()),
                    "ChoiceLimit": 2,
                    "Description": ["Sample description"],
                },
            ],
            "BallotType": {"Name": "Simple"},
            "ObjectType": "BallotProposal",
            "ProposalId": str(uuid.uuid4()),
            "VoteEndEpoch": 202,
            "ObjectVersion": "1.0.0",
            "SnapshotEpoch": 200,
            "VoteStartEpoch": 201,
        }
    }

    tx_hash = create_proposal(
        creator, proposal_metadata, lovelace_fee, PLATFORM_ADDRESS
    )

    print(f"Successfully submitted proposal {tx_hash}")

    timeout = 4 * 60 + 20  # Max delay for the transaction to get on-chain
    start_time = datetime.datetime.now()

    while True:
        process = ProcessedLog.query.filter(ProcessedLog.tx_hash == tx_hash).first()

        if process is not None:
            print("Finally! Found a matching process!")

            assert process.success == True
            assert process.valid == True
            assert process.tx_metadata == proposal_metadata[1916]

            proposal = Proposal.query.filter(Proposal.id == process.proposal_id).first()
            assert proposal is not None
            assert proposal.status == "on-chain"

            break

        current_time = datetime.datetime.now()

        assert (
            start_time + datetime.timedelta(seconds=timeout) >= current_time
        ), "timeout expired"

        sleep(5)

    vote_metadata = {
        1916: {
            "ObjectType": "VoteBallot",
            "ObjectVersion": "1.0.0",
            "VoteId": str(uuid.uuid4()),
            "ProposalId": proposal_metadata[1916]["ProposalId"],
            "Choices": [
                {
                    "QuestionId": str(uuid.uuid4()),
                    "ChoiceId": proposal_metadata[1916]["Questions"][0]["Choices"][1][
                        "ChoiceId"
                    ],
                },
                {
                    "QuestionId": proposal_metadata[1916]["Questions"][1]["QuestionId"],
                    "ChoiceId": proposal_metadata[1916]["Questions"][1]["Choices"][0][
                        "ChoiceId"
                    ],
                },
                {
                    "QuestionId": proposal_metadata[1916]["Questions"][1]["QuestionId"],
                    "ChoiceId": proposal_metadata[1916]["Questions"][1]["Choices"][2][
                        "ChoiceId"
                    ],
                },
            ],
        }
    }

    tx_hash = create_vote("bob", vote_metadata)
    print(f"Successfully submitted vote {tx_hash}")

    timeout = 4 * 60 + 20  # Max delay for the transaction to get on-chain
    start_time = datetime.datetime.now()

    while True:
        process = ProcessedLog.query.filter(ProcessedLog.tx_hash == tx_hash).first()

        if process is not None:
            print("Finally! Found a matching process!")

            assert process.success == True
            assert process.valid == False
            assert process.tx_metadata == vote_metadata[1916]

            vote = Vote.query.filter(Vote.id == process.vote_id).first()
            assert vote is None

            break

        current_time = datetime.datetime.now()

        assert (
            start_time + datetime.timedelta(seconds=timeout) >= current_time
        ), "timeout expired"

        sleep(5)


def test_inexistent_choice_vote(session):
    sys.path.append("src")

    from model.processed_log import ProcessedLog
    from model.proposal import Proposal
    from model.vote import Vote

    creator = "alice"
    voter = "bob"
    lovelace_fee = 2_000_000

    proposal_metadata = {
        1916: {
            "Title": "Friends Trivia",
            "NetworkId": "Voteaire - Testing",
            "Questions": [
                {
                    "Choices": [
                        {
                            "Name": "Accountant",
                            "ChoiceId": str(uuid.uuid4()),
                        },
                        {
                            "Name": "Statistical Analysis",
                            "ChoiceId": str(uuid.uuid4()),
                        },
                        {
                            "Name": "Graphic Designer",
                            "ChoiceId": str(uuid.uuid4()),
                        },
                    ],
                    "Question": ["What was Chandler's job?"],
                    "QuestionId": str(uuid.uuid4()),
                    "ChoiceLimit": 1,
                },
                {
                    "Choices": [
                        {
                            "Name": "Alice",
                            "ChoiceId": str(uuid.uuid4()),
                        },
                        {
                            "Name": "Erika",
                            "ChoiceId": str(uuid.uuid4()),
                        },
                        {
                            "Name": "Ursula",
                            "ChoiceId": str(uuid.uuid4()),
                        },
                    ],
                    "Question": ["What was the name of Phoeby's twin sister?"],
                    "QuestionId": str(uuid.uuid4()),
                    "ChoiceLimit": 2,
                    "Description": ["Sample description"],
                },
            ],
            "BallotType": {"Name": "Simple"},
            "ObjectType": "BallotProposal",
            "ProposalId": str(uuid.uuid4()),
            "VoteEndEpoch": 202,
            "ObjectVersion": "1.0.0",
            "SnapshotEpoch": 200,
            "VoteStartEpoch": 201,
        }
    }

    tx_hash = create_proposal(
        creator, proposal_metadata, lovelace_fee, PLATFORM_ADDRESS
    )

    print(f"Successfully submitted proposal {tx_hash}")

    timeout = 4 * 60 + 20  # Max delay for the transaction to get on-chain
    start_time = datetime.datetime.now()

    while True:
        process = ProcessedLog.query.filter(ProcessedLog.tx_hash == tx_hash).first()

        if process is not None:
            print("Finally! Found a matching process!")

            assert process.success == True
            assert process.valid == True
            assert process.tx_metadata == proposal_metadata[1916]

            proposal = Proposal.query.filter(Proposal.id == process.proposal_id).first()
            assert proposal is not None
            assert proposal.status == "on-chain"

            break

        current_time = datetime.datetime.now()

        assert (
            start_time + datetime.timedelta(seconds=timeout) >= current_time
        ), "timeout expired"

        sleep(5)

    vote_metadata = {
        1916: {
            "ObjectType": "VoteBallot",
            "ObjectVersion": "1.0.0",
            "VoteId": str(uuid.uuid4()),
            "ProposalId": proposal_metadata[1916]["ProposalId"],
            "Choices": [
                {
                    "QuestionId": proposal_metadata[1916]["Questions"][0]["QuestionId"],
                    "ChoiceId": str(uuid.uuid4()),
                },
                {
                    "QuestionId": proposal_metadata[1916]["Questions"][1]["QuestionId"],
                    "ChoiceId": proposal_metadata[1916]["Questions"][1]["Choices"][0][
                        "ChoiceId"
                    ],
                },
                {
                    "QuestionId": proposal_metadata[1916]["Questions"][1]["QuestionId"],
                    "ChoiceId": proposal_metadata[1916]["Questions"][1]["Choices"][2][
                        "ChoiceId"
                    ],
                },
            ],
        }
    }

    tx_hash = create_vote("bob", vote_metadata)
    print(f"Successfully submitted vote {tx_hash}")

    timeout = 4 * 60 + 20  # Max delay for the transaction to get on-chain
    start_time = datetime.datetime.now()

    while True:
        process = ProcessedLog.query.filter(ProcessedLog.tx_hash == tx_hash).first()

        if process is not None:
            print("Finally! Found a matching process!")

            assert process.success == True
            assert process.valid == False
            assert process.tx_metadata == vote_metadata[1916]

            vote = Vote.query.filter(Vote.id == process.vote_id).first()
            assert vote is None

            break

        current_time = datetime.datetime.now()

        assert (
            start_time + datetime.timedelta(seconds=timeout) >= current_time
        ), "timeout expired"

        sleep(5)

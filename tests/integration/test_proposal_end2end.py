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


def test_create_proposal_success(session):
    sys.path.append("src")

    from model.processed_log import ProcessedLog
    from model.proposal import Proposal

    creator = "alice"
    creator_info = load_user(creator)
    creator_addr = creator_info["stake_address"]

    r = requests.post(
        f"{API_ENDPOINT}/proposal/create",
        json={
            "version": "1.0.0",
            "network_id": "Voteaire - Testing",
            "title": "Friends Trivia",
            "ballot_type": {"name": "Simple"},
            "creator_stake_address": creator_addr,
            "questions": [
                {
                    "question": "What was Chandler's job?",
                    "choice_limit": 1,
                    "choices": [
                        {"choice": "Accountant"},
                        {"choice": "Statistical Analysis"},
                        {"choice": "Graphic Designer"},
                    ],
                },
                {
                    "question": "What was the name of Phoeby's twin sister?",
                    "description": "Sample description",
                    "choice_limit": 2,
                    "choices": [
                        {"choice": "Alice"},
                        {"choice": "Erika"},
                        {"choice": "Ursula"},
                    ],
                },
            ],
            "start_epoch": 203,
            "end_epoch": 203,
            "snapshot_epoch": 200,
        },
    )

    if r.status_code != 200:
        print(r.reason)
        assert r.status_code == 200  # Redundant on purpose

    response = r.json()

    print("Success submitting draft proposal!")

    lovelace_fee = response["lovelace_fee"]
    metadata = {1916: json.loads(response["metadata"])}

    tx_hash = create_proposal(creator, metadata, lovelace_fee, PLATFORM_ADDRESS)

    print(
        f"Successfully sent proposal metadata transaction with transaction hash {tx_hash}!"
    )

    timeout = 4 * 60 + 20  # Max delay for the transaction to get on-chain
    start_time = datetime.datetime.now()

    while True:
        process = ProcessedLog.query.filter(ProcessedLog.tx_hash == tx_hash).first()

        if process is not None:
            print("Finally! Found a matching process!")

            assert process.success == True
            assert process.valid == True
            assert process.tx_metadata == json.loads(response["metadata"])

            proposal = Proposal.query.filter(Proposal.id == process.proposal_id).first()
            assert proposal is not None
            assert proposal.status == "on-chain"

            break

        current_time = datetime.datetime.now()

        assert (
            start_time + datetime.timedelta(seconds=timeout) >= current_time
        ), "timeout expired"

        sleep(5)


def test_create_manual_proposal(session):
    sys.path.append("src")

    from model.processed_log import ProcessedLog
    from model.proposal import Proposal

    creator = "alice"
    lovelace_fee = 2_000_000

    metadata = {
        1916: {
            "Title": "Very intersting title",
            "NetworkId": "Voteaire - Testing",
            "Questions": [
                {
                    "Question": ["Very interesting question?"],
                    "QuestionId": str(uuid.uuid4()),
                    "ChoiceLimit": 1,
                    "Choices": [
                        {
                            "ChoiceId": str(uuid.uuid4()),
                            "Name": "Very interesting option",
                        },
                    ],
                }
            ],
            "BallotType": {"Name": "Simple"},
            "ObjectType": "BallotProposal",
            "ProposalId": str(uuid.uuid4()),
            "VoteEndEpoch": 203,
            "ObjectVersion": "1.0.0",
            "SnapshotEpoch": 200,
            "VoteStartEpoch": 203,
        }
    }

    tx_hash = create_proposal(creator, metadata, lovelace_fee, PLATFORM_ADDRESS)

    print(
        f"Successfully sent proposal metadata transaction with transaction hash {tx_hash}!"
    )

    timeout = 4 * 60 + 20  # Max delay for the transaction to get on-chain
    start_time = datetime.datetime.now()

    while True:
        process = ProcessedLog.query.filter(ProcessedLog.tx_hash == tx_hash).first()

        if process is not None:
            print("Finally! Found a matching process!")

            assert process.success == True
            assert process.valid == True
            assert process.tx_metadata == metadata[1916]

            proposal = Proposal.query.filter(Proposal.id == process.proposal_id).first()
            assert proposal is not None
            assert proposal.status == "on-chain"

            break

        current_time = datetime.datetime.now()

        assert (
            start_time + datetime.timedelta(seconds=timeout) >= current_time
        ), "timeout expired"

        sleep(5)


def test_proposal_wrong_schema(session):
    sys.path.append("src")

    from model.processed_log import ProcessedLog
    from model.proposal import Proposal

    creator = "alice"
    lovelace_fee = 2_000_000

    metadata = {
        1916: {
            "Title": "Very intersting title",
            "NetworkId": "Voteaire - Testing",
            "Questions": [
                {
                    "Question": ["Very interesting question?"],
                    "QuestionId": str(uuid.uuid4()),
                    "ChoiceLimit": 1,
                    "Choices": [
                        {
                            "ChoiceId": str(uuid.uuid4()),
                            "Name": "Very interesting option",
                        },
                    ],
                }
            ],
            "BallotType": {"Name": "Simple"},
            "ObjectType": "BallotProposal",
            "ProposalId": str(uuid.uuid4()),
            "VoteEndEpoch": 203,
            "ObjectVersion": "7.7.7",
            "SnapshotEpoch": 200,
            "VoteStartEpoch": 203,
        }
    }

    tx_hash = create_proposal(creator, metadata, lovelace_fee, PLATFORM_ADDRESS)

    print(
        f"Successfully sent proposal metadata transaction with transaction hash {tx_hash}!"
    )

    timeout = 4 * 60 + 20  # Max delay for the transaction to get on-chain
    start_time = datetime.datetime.now()

    while True:
        process = ProcessedLog.query.filter(ProcessedLog.tx_hash == tx_hash).first()

        if process is not None:
            print("Finally! Found a matching process!")

            assert process.success == True
            assert process.valid == False
            assert process.tx_metadata == metadata[1916]

            proposal = Proposal.query.filter(Proposal.id == process.proposal_id).first()
            assert proposal is None

            break

        current_time = datetime.datetime.now()

        assert (
            start_time + datetime.timedelta(seconds=timeout) >= current_time
        ), "timeout expired"

        sleep(5)


def test_proposal_existing_question(session):
    sys.path.append("src")

    from model.processed_log import ProcessedLog
    from model.proposal import Proposal

    proposal = fake_proposal(session, add_to_db=True)
    question_identifier = proposal.questions[0].question_identifier

    creator = "alice"
    lovelace_fee = 2_000_000

    metadata = {
        1916: {
            "Title": "Very intersting title",
            "NetworkId": "Voteaire - Testing",
            "Questions": [
                {
                    "Question": ["Very interesting question?"],
                    "QuestionId": question_identifier,
                    "ChoiceLimit": 1,
                    "Choices": [
                        {
                            "ChoiceId": str(uuid.uuid4()),
                            "Name": "Very interesting option",
                        },
                    ],
                }
            ],
            "BallotType": {"Name": "Simple"},
            "ObjectType": "BallotProposal",
            "ProposalId": str(uuid.uuid4()),
            "VoteEndEpoch": 203,
            "ObjectVersion": "1.0.0",
            "SnapshotEpoch": 200,
            "VoteStartEpoch": 203,
        }
    }

    tx_hash = create_proposal(creator, metadata, lovelace_fee, PLATFORM_ADDRESS)

    print(
        f"Successfully sent proposal metadata transaction with transaction hash {tx_hash}!"
    )

    timeout = 4 * 60 + 20  # Max delay for the transaction to get on-chain
    start_time = datetime.datetime.now()

    while True:
        process = ProcessedLog.query.filter(ProcessedLog.tx_hash == tx_hash).first()

        if process is not None:
            print("Finally! Found a matching process!")

            assert process.success == True
            assert process.valid == False
            assert process.tx_metadata == metadata[1916]

            proposal = Proposal.query.filter(Proposal.id == process.proposal_id).first()
            assert proposal is None

            break

        current_time = datetime.datetime.now()

        assert (
            start_time + datetime.timedelta(seconds=timeout) >= current_time
        ), "timeout expired"

        sleep(5)


def test_proposal_existing_choice(session):
    sys.path.append("src")

    from model.processed_log import ProcessedLog
    from model.proposal import Proposal

    proposal = fake_proposal(session, add_to_db=True)
    choice_identifier = proposal.questions[0].choices[0].choice_identifier

    creator = "alice"
    lovelace_fee = 2_000_000

    metadata = {
        1916: {
            "Title": "Very intersting title",
            "NetworkId": "Voteaire - Testing",
            "Questions": [
                {
                    "Question": ["Very interesting question?"],
                    "QuestionId": str(uuid.uuid4()),
                    "ChoiceLimit": 1,
                    "Choices": [
                        {
                            "ChoiceId": choice_identifier,
                            "Name": "Very interesting option",
                        },
                    ],
                }
            ],
            "BallotType": {"Name": "Simple"},
            "ObjectType": "BallotProposal",
            "ProposalId": str(uuid.uuid4()),
            "VoteEndEpoch": 203,
            "ObjectVersion": "1.0.0",
            "SnapshotEpoch": 200,
            "VoteStartEpoch": 203,
        }
    }

    tx_hash = create_proposal(creator, metadata, lovelace_fee, PLATFORM_ADDRESS)

    print(
        f"Successfully sent proposal metadata transaction with transaction hash {tx_hash}!"
    )

    timeout = 4 * 60 + 20  # Max delay for the transaction to get on-chain
    start_time = datetime.datetime.now()

    while True:
        process = ProcessedLog.query.filter(ProcessedLog.tx_hash == tx_hash).first()

        if process is not None:
            print("Finally! Found a matching process!")

            assert process.success == True
            assert process.valid == False
            assert process.tx_metadata == metadata[1916]

            proposal = Proposal.query.filter(Proposal.id == process.proposal_id).first()
            assert proposal is None

            break

        current_time = datetime.datetime.now()

        assert (
            start_time + datetime.timedelta(seconds=timeout) >= current_time
        ), "timeout expired"

        sleep(5)


def test_proposal_start_after_end(session):
    sys.path.append("src")

    from model.processed_log import ProcessedLog
    from model.proposal import Proposal

    creator = "alice"
    lovelace_fee = 2_000_000

    metadata = {
        1916: {
            "Title": "Very intersting title",
            "NetworkId": "Voteaire - Testing",
            "Questions": [
                {
                    "Question": ["Very interesting question?"],
                    "QuestionId": str(uuid.uuid4()),
                    "ChoiceLimit": 1,
                    "Choices": [
                        {
                            "ChoiceId": str(uuid.uuid4()),
                            "Name": "Very interesting option",
                        },
                    ],
                }
            ],
            "BallotType": {"Name": "Simple"},
            "ObjectType": "BallotProposal",
            "ProposalId": str(uuid.uuid4()),
            "VoteEndEpoch": 203,
            "ObjectVersion": "1.0.0",
            "SnapshotEpoch": 200,
            "VoteStartEpoch": 204,
        }
    }

    tx_hash = create_proposal(creator, metadata, lovelace_fee, PLATFORM_ADDRESS)

    print(
        f"Successfully sent proposal metadata transaction with transaction hash {tx_hash}!"
    )

    timeout = 4 * 60 + 20  # Max delay for the transaction to get on-chain
    start_time = datetime.datetime.now()

    while True:
        process = ProcessedLog.query.filter(ProcessedLog.tx_hash == tx_hash).first()

        if process is not None:
            print("Finally! Found a matching process!")

            assert process.success == True
            assert process.valid == False
            assert process.tx_metadata == metadata[1916]

            proposal = Proposal.query.filter(Proposal.id == process.proposal_id).first()
            assert proposal is None

            break

        current_time = datetime.datetime.now()

        assert (
            start_time + datetime.timedelta(seconds=timeout) >= current_time
        ), "timeout expired"

        sleep(5)


def test_proposal_snapshot_after_end(session):
    sys.path.append("src")

    from model.processed_log import ProcessedLog
    from model.proposal import Proposal

    creator = "alice"
    lovelace_fee = 2_000_000

    metadata = {
        1916: {
            "Title": "Very intersting title",
            "NetworkId": "Voteaire - Testing",
            "Questions": [
                {
                    "Question": ["Very interesting question?"],
                    "QuestionId": str(uuid.uuid4()),
                    "ChoiceLimit": 1,
                    "Choices": [
                        {
                            "ChoiceId": str(uuid.uuid4()),
                            "Name": "Very interesting option",
                        },
                    ],
                }
            ],
            "BallotType": {"Name": "Simple"},
            "ObjectType": "BallotProposal",
            "ProposalId": str(uuid.uuid4()),
            "VoteEndEpoch": 204,
            "ObjectVersion": "1.0.0",
            "SnapshotEpoch": 205,
            "VoteStartEpoch": 203,
        }
    }

    tx_hash = create_proposal(creator, metadata, lovelace_fee, PLATFORM_ADDRESS)

    print(
        f"Successfully sent proposal metadata transaction with transaction hash {tx_hash}!"
    )

    timeout = 4 * 60 + 20  # Max delay for the transaction to get on-chain
    start_time = datetime.datetime.now()

    while True:
        process = ProcessedLog.query.filter(ProcessedLog.tx_hash == tx_hash).first()

        if process is not None:
            print("Finally! Found a matching process!")

            assert process.success == True
            assert process.valid == False
            assert process.tx_metadata == metadata[1916]

            proposal = Proposal.query.filter(Proposal.id == process.proposal_id).first()
            assert proposal is None

            break

        current_time = datetime.datetime.now()

        assert (
            start_time + datetime.timedelta(seconds=timeout) >= current_time
        ), "timeout expired"

        sleep(5)

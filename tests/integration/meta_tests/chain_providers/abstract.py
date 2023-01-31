import sys


def test_chain_provider(chain_provider):
    sys.path.append("src")

    assert chain_provider.get_metadata_entries("1916", 2, 1) == [
        {
            "tx_hash": "a92f33f2c86d3a34d94b4e41d9f0dd2a040cddb6e4cb4dd130fcbb9850ca1767",
            "json_metadata": {
                "747059737117921": {
                    "Title": "Yes or no",
                    "NetworkId": "Voteaire - WildWarriors",
                    "Questions": [
                        {
                            "Choices": [
                                {
                                    "Name": "Yes",
                                    "ChoiceId": "a2a49763-39cd-42cc-8e76-901b4f7f9672",
                                    "Description": "",
                                },
                                {
                                    "Name": "No",
                                    "ChoiceId": "5bbbeaac-cc6d-4179-9361-0aa9705d18c8",
                                    "Description": "",
                                },
                            ],
                            "Question": ["Yes?"],
                            "QuestionId": "127400de-d00a-4397-bcc4-2a98c5b274ba",
                            "ChoiceLimit": 1,
                        }
                    ],
                    "BallotType": {"Name": "Simple", "SnapshotEpoch": 231},
                    "ObjectType": "VoteProposal",
                    "ProposalId": "bead0259-45cb-495e-ad2e-9c42e67359ee",
                    "ProposalURL": "",
                    "VoteEndEpoch": 231,
                    "ObjectVersion": "1.0.0",
                    "VoteStartEpoch": 231,
                }
            },
        },
        {
            "tx_hash": "dbe511e0a411c24c38e542568c1a9eab15c4faa413111c8ec44dd0af7ec6cbb9",
            "json_metadata": {
                "Title": "Yes or no",
                "NetworkId": "Fake :)",
                "Questions": [
                    {
                        "Choices": [
                            {
                                "Name": "Yes",
                                "ChoiceId": "d6a12ea7-2d72-4bb9-b189-367e1e9e5548",
                                "Description": [],
                            },
                            {
                                "Name": "No",
                                "ChoiceId": "6d69663d-ca56-4c92-ab0b-2829a219080a",
                                "Description": [],
                            },
                        ],
                        "Question": ["Yes?"],
                        "QuestionId": "88094527-f4bd-4e74-a939-5e33d08e8cbc",
                        "ChoiceLimit": 1,
                    }
                ],
                "BallotType": {"Name": "Simple", "SnapshotEpoch": 231},
                "ObjectType": "VoteProposal",
                "ProposalId": "3c04cc01-4a1e-4658-94a5-0d526230d2a5",
                "Description": ["huh"],
                "ProposalURL": "https://example.com",
                "VoteEndEpoch": 231,
                "ObjectVersion": "1.0.0",
                "VoteStartEpoch": 231,
            },
        },
    ]

    assert chain_provider.get_transaction_info(
        "862df6635f9344f031baa3b9af7d8be1a86136a07265cf342891c3804c09145f"
    ) == {
        "hash": "862df6635f9344f031baa3b9af7d8be1a86136a07265cf342891c3804c09145f",
        "block": "74bb5c5651f8ddba07ec159e71105a7934b6f9aaad8eef8f37f7b1f8988c42f9",
        "block_height": 3458713,
        "block_time": 1649412845,
        "slot": 55043629,
        "index": 2,
        "output_amount": [{"unit": "lovelace", "quantity": "1250131456"}],
        "fees": "171397",
        "deposit": "0",
        "size": 289,
        "invalid_before": None,
        "invalid_hereafter": "55050740",
        "utxo_count": 3,
        "withdrawal_count": 0,
        "mir_cert_count": 0,
        "delegation_count": 0,
        "stake_cert_count": 0,
        "pool_update_count": 0,
        "pool_retire_count": 0,
        "asset_mint_or_burn_count": 0,
        "redeemer_count": 0,
        "valid_contract": True,
    }

    assert chain_provider.get_transaction_inputs(
        "862df6635f9344f031baa3b9af7d8be1a86136a07265cf342891c3804c09145f"
    ) == [
        {
            "address": "addr_test1qqj09vv9zv3dyy67gcllgsjg4rajhl9n3c8n7fsp6dx7h26grspnn63ax27a89h2r3d638qvmxmrvex4wf8raptgr9tqmy293l",
            "amount": [{"unit": "lovelace", "quantity": "1250302853"}],
            "tx_hash": "10a457c248c7d608987f50ae2e5c1433e662ae7cfd5391f7d486758f52ebf965",
            "output_index": 1,
            "collateral": False,
            "data_hash": None,
        }
    ]

    assert chain_provider.get_transaction_outputs(
        "862df6635f9344f031baa3b9af7d8be1a86136a07265cf342891c3804c09145f"
    ) == [
        {
            "address": "addr_test1qzcfjkkx748dnzd0cfqhthxmdmcq6a4v8nmdw2atlrvj9njymypaafxkmfq5yj3wfpc55u4als0m33mh5ulc2fg6kksq57htfn",
            "amount": [{"unit": "lovelace", "quantity": "6000000"}],
            "output_index": 0,
            "data_hash": None,
        },
        {
            "address": "addr_test1qqj09vv9zv3dyy67gcllgsjg4rajhl9n3c8n7fsp6dx7h26grspnn63ax27a89h2r3d638qvmxmrvex4wf8raptgr9tqmy293l",
            "amount": [{"unit": "lovelace", "quantity": "1244131456"}],
            "output_index": 1,
            "data_hash": None,
        },
    ]

    assert (
        chain_provider.get_lovelace_sent(
            "862df6635f9344f031baa3b9af7d8be1a86136a07265cf342891c3804c09145f",
            "addr_test1qzcfjkkx748dnzd0cfqhthxmdmcq6a4v8nmdw2atlrvj9njymypaafxkmfq5yj3wfpc55u4als0m33mh5ulc2fg6kksq57htfn",
        )
        == 6_000_000
    )

    assert (
        chain_provider.get_sender_address(
            "862df6635f9344f031baa3b9af7d8be1a86136a07265cf342891c3804c09145f"
        )
        == "addr_test1qqj09vv9zv3dyy67gcllgsjg4rajhl9n3c8n7fsp6dx7h26grspnn63ax27a89h2r3d638qvmxmrvex4wf8raptgr9tqmy293l"
    )

    assert chain_provider.get_address_info(
        "addr_test1qrqh9tujjtckenpq9qfs867zma8r6nka7rm6czmcxrqn90xwh8v2xf3tcutgsu2cmj4gz908gke4s6g8ynu8k3anu88qmexesq"
    ) == {
        "address": "addr_test1qrqh9tujjtckenpq9qfs867zma8r6nka7rm6czmcxrqn90xwh8v2xf3tcutgsu2cmj4gz908gke4s6g8ynu8k3anu88qmexesq",
        "amount": [{"unit": "lovelace", "quantity": "6000000"}],
        "stake_address": "stake_test1ur8tnk9ryc4uw95gw9vde25pzhn5tv6cdyrjf7rmg7e7rns7raxx7",
        "type": "shelley",
        "script": False,
    }

    assert chain_provider.get_epoch_snapshot(
        "stake_test1uqmua3stfp60dlwkxfh8jk7d49tu9u2de9q0vul9mdcgd6gasp4mx", 160
    ) == {
        "active_epoch": 160,
        "amount": "99052970280613",
        "pool_id": "pool1e5m6zeq0e9xnrwj8leypn2045yxme4jh98gnyptwv6wz5lz90mg",
    }

def get_metadata_entries(label: str, count: int = None, page: int = None):
    if count is None:
        count = 100
    if page is None:
        page = 1

    max_page = 10
    if page > max_page:
        return None

    return [
        {"tx_hash": f"HASH{page}-{i+1}", "json_metadata": {"foo": f"bar{page}-{i+1}"}}
        for i in range(count)
    ]


def get_transaction_info(tx_hash):
    return {
        "hash": "HASH1",
        "block": "356b7d7dbb696ccd12775c016941057a9dc70898d87a63fc752271bb46856940",
        "block_height": 123456,
        "block_time": 1635505891,
        "slot": 42000000,
        "index": 1,
        "output_amount": [
            {"unit": "lovelace", "quantity": "42000000"},
            {
                "unit": "b0d07d45fe9514f80213f4020e5a61241458be626841cde717cb38a76e7574636f696e",
                "quantity": "12",
            },
        ],
        "fees": "182485",
        "deposit": "0",
        "size": 433,
        "invalid_before": None,
        "invalid_hereafter": "13885913",
        "utxo_count": 4,
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


def get_transaction_inputs(tx_hash):
    return [
        {
            "address": "ADDR1",
            "amount": [{"unit": "lovelace", "quantity": "100000000"}],
            "tx_hash": "HASH1",
            "output_index": 0,
            "collateral": False,
            "data_hash": None,
        },
        {
            "address": "ADDR1",
            "amount": [{"unit": "lovelace", "quantity": "50000000"}],
            "tx_hash": "HASH1",
            "output_index": 1,
            "collateral": False,
            "data_hash": None,
        },
        {
            "address": "ADDR2",
            "amount": [{"unit": "lovelace", "quantity": "200000000"}],
            "tx_hash": "HASH2",
            "output_index": 2,
            "collateral": False,
            "data_hash": None,
        },
    ]


def get_transaction_outputs(tx_hash):
    return [
        {
            "address": "ADDR1",
            "amount": [{"unit": "lovelace", "quantity": "100000000"}],
            "tx_hash": tx_hash,
            "output_index": 0,
            "collateral": False,
            "data_hash": None,
        },
        {
            "address": "ADDR1",
            "amount": [{"unit": "lovelace", "quantity": "50000000"}],
            "tx_hash": tx_hash,
            "output_index": 1,
            "collateral": False,
            "data_hash": None,
        },
        {
            "address": "ADDR2",
            "amount": [{"unit": "lovelace", "quantity": "200000000"}],
            "tx_hash": tx_hash,
            "output_index": 2,
            "collateral": False,
            "data_hash": None,
        },
    ]


def get_lovelace_sent(tx_hash, receiving_address):
    return 150_000_000


def get_sender_address(tx_hash):
    return "ADDR1"


def get_address_info(address):
    return {
        "address": address,
        "amount": [{"unit": "lovelace", "quantity": "6000000"}],
        "stake_address": "stake_test1ur8tnk9ryc4uw95gw9vde25pzhn5tv6cdyrjf7rmg7e7rns7raxx7",
        "type": "shelley",
        "script": False,
    }


# Functions that start with helper are not required
# by the chain providers and are here just to help
# mock them
def helper_get_address_info_without_stake_address(address):
    return {
        "address": address,
        "amount": [{"unit": "lovelace", "quantity": "6000000"}],
        "type": "shelley",
        "script": False,
    }


def get_epoch_snapshot(staking_address, epoch_no):
    return {"active_epoch": epoch_no, "amount": "4882704265", "pool_id": "pool123"}


def get_current_epoch():
    return {
        "epoch": 196,
        "start_time": 1738713600,
        "end_time": 1739145600,
        "first_block_time": 1648671619,
        "last_block_time": 1648757566,
        "block_count": 2416,
        "tx_count": 10428,
        "output": "45380862611286119",
        "fees": "4060876833",
        "active_stake": "15040299321704596",
    }


def get_protocol_parameters():
    return {
        "epoch": 196,
        "min_fee_a": 44,
        "min_fee_b": 155381,
        "max_block_size": 98304,
        "max_tx_size": 16384,
        "max_block_header_size": 1100,
        "key_deposit": "2000000",
        "pool_deposit": "500000000",
        "e_max": 18,
        "n_opt": 500,
        "a0": 0.3,
        "rho": 0.003,
        "tau": 0.2,
        "decentralisation_param": 0,
        "extra_entropy": None,
        "protocol_major_ver": 6,
        "protocol_minor_ver": 0,
        "min_utxo": "34482",
        "min_pool_cost": "340000000",
        "nonce": "d501bc1c8f116f938bc5e1ad1fb5d29858cf75eb1af9701459930a33b2cebe8a",
        "price_mem": 0.0577,
        "price_step": 0.0000721,
        "max_tx_ex_mem": "16000000",
        "max_tx_ex_steps": "10000000000",
        "max_block_ex_mem": "80000000",
        "max_block_ex_steps": "40000000000",
        "max_val_size": "5000",
        "collateral_percent": 150,
        "max_collateral_inputs": 3,
        "coins_per_utxo_word": "34482",
    }

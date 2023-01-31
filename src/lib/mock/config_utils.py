def get_fees(ballot_type: str) -> int:
    fees = {"Simple": 10_000_000, "Delegated": 20_000_000, "PolicyId": 30_000_000}

    if not ballot_type in fees:
        raise ValueError(f"Config key {ballot_type.lower()}_fees does not exist!")

    return fees[ballot_type]

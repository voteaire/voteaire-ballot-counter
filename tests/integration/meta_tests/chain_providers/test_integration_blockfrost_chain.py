import sys


def test_blockfrost():
    sys.path.append("src")

    from meta.chain_providers import blockfrost
    from abstract import test_chain_provider

    test_chain_provider(blockfrost)

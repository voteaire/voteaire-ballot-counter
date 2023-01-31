import sys


def test_dbsync():
    sys.path.append("src")

    from meta.chain_providers import dbsync
    from abstract import test_chain_provider

    # Skipping this test while dbsync is not ready
    # test_chain_provider(dbsync)

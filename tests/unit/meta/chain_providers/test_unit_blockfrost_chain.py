# Doesn't make sense to test the API it self
# But I think it's a good idea to make sure we have
# all mock methods implemented in blockfrost

import sys

from inspect import getmembers, isfunction


def test_methods(mocker):
    sys.path.append("src")

    mocker.patch("meta.chain_providers.blockfrost.BlockFrostApi", None)

    import meta.chain_providers.blockfrost as blockfrost
    import meta.chain_providers.mock as mock

    blockfrost_functions = [f[0] for f in getmembers(blockfrost, isfunction)]
    mock_functions = [f[0] for f in getmembers(mock, isfunction)]

    for function_name in mock_functions:
        if not function_name[:6] == "helper":
            # Functions that start with helper are not required
            # by the chain providers and are here just to help
            # mock them

            assert function_name in blockfrost_functions

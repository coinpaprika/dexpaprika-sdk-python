from datetime import timedelta

import pytest

from dexpaprika_sdk import DexPaprikaClient


@pytest.fixture
def api():
    return DexPaprikaClient().tokens


@pytest.mark.parametrize(
    "endpoint, expected",
    [
        ("/networks", timedelta(hours=24)),
        ("/networks/ethereum/dexes", timedelta(hours=24)),
        ("/networks/ethereum/tokens/0xabc/ohlcv", timedelta(minutes=1)),
        ("/networks/ethereum/pools/0xp/ohlcv", timedelta(minutes=1)),
        ("/networks/ethereum/pools/0xp/transactions", timedelta(minutes=1)),
        ("/networks/ethereum/multi/prices", timedelta(minutes=1)),
        ("/networks/ethereum/pools/search", timedelta(minutes=5)),
        ("/networks/ethereum/tokens/0xabc", timedelta(minutes=10)),
        ("/stats", timedelta(minutes=15)),
    ],
)
def test_ttl_follows_what_the_path_returns(api, endpoint, expected):
    assert api._get_ttl(endpoint) == expected


def test_nothing_under_a_network_inherits_the_network_list_ttl(api):
    # Every data path starts with /networks/; only the lists themselves
    # may be cached for a day.
    assert api._get_ttl("/networks/solana/tokens/So11111111111111111111111111111111111111112") < timedelta(hours=1)

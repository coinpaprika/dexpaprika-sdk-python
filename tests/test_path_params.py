"""
Ids that go into the request path.

Every method that puts a network id, pool address or token address into the URL
path must refuse a value that would change that path or add a query, and must
send a real id exactly as given. The session is patched, so no request leaves
the process.
"""

from unittest.mock import patch
from urllib.parse import urlsplit

import pytest

from dexpaprika_sdk import DexPaprikaClient

POOL = "0x88e6a0c2ddd26feeb64f039a2c41296fcb3f5640"
TOKEN = "0xc02aaa39b223fe8d0a0e5c4f27ead9083c756cc2"


class _Sent(Exception):
    """Raised by the patched session once it has recorded the URL."""


def _recording_client(seen):
    client = DexPaprikaClient(max_retries=0)

    def request(method, url, **kwargs):
        seen.append(urlsplit(url).path)
        raise _Sent()

    return client, patch.object(client.session, "request", side_effect=request)


# Every method that builds a path from caller input. `n` is the network id, `a`
# the pool or token address; ADDRESS_CALLS put `a` into the path as well.
NETWORK_CALLS = {
    "pools.list_by_network": lambda c, n, a: c.pools.list_by_network(n),
    "pools.list_by_dex": lambda c, n, a: c.pools.list_by_dex(n, "uniswap_v3"),
    "pools.filter": lambda c, n, a: c.pools.filter(n),
    "tokens.get_pools": lambda c, n, a: c.tokens.get_pools(n, TOKEN),
    "tokens.get_top": lambda c, n, a: c.tokens.get_top(n),
    "tokens.filter": lambda c, n, a: c.tokens.filter(n),
    "tokens.get_multi_prices": lambda c, n, a: c.tokens.get_multi_prices(n, [TOKEN]),
    "networks.list_dexes": lambda c, n, a: c.networks.list_dexes(n),
    "dexes.list": lambda c, n, a: c.dexes.list(n),
}
ADDRESS_CALLS = {
    "pools.get_details": lambda c, n, a: c.pools.get_details(n, a),
    "pools.get_ohlcv": lambda c, n, a: c.pools.get_ohlcv(n, a, start="-24h", interval="1h"),
    "pools.get_transactions": lambda c, n, a: c.pools.get_transactions(n, a),
    "pools.get_indicator": lambda c, n, a: c.pools.get_indicator(n, a, indicator="rsi"),
    "tokens.get_details": lambda c, n, a: c.tokens.get_details(n, a),
    "tokens.get_ohlcv": lambda c, n, a: c.tokens.get_ohlcv(n, a, start="-24h", interval="1h"),
    "tokens.get_indicator": lambda c, n, a: c.tokens.get_indicator(n, a, indicator="rsi"),
}

BAD = [
    ".", "..", "../../usage", "../../../stats", "eth/../x", "a\\b", "x?limit=1000", "x#y",
    "%2e%2e", "..%2Fusage", "a b", "a\nb", "a\x00b",
]


@pytest.mark.parametrize("name", sorted({**NETWORK_CALLS, **ADDRESS_CALLS}))
@pytest.mark.parametrize("bad", BAD)
def test_network_id_that_leaves_its_segment_is_refused_before_sending(name, bad):
    call = {**NETWORK_CALLS, **ADDRESS_CALLS}[name]
    seen = []
    client, patched = _recording_client(seen)
    with patched, pytest.raises(ValueError, match="network"):
        call(client, bad, POOL)
    assert seen == []


@pytest.mark.parametrize("name", sorted(ADDRESS_CALLS))
@pytest.mark.parametrize("bad", BAD)
def test_address_that_leaves_its_segment_is_refused_before_sending(name, bad):
    seen = []
    client, patched = _recording_client(seen)
    with patched, pytest.raises(ValueError, match="address"):
        ADDRESS_CALLS[name](client, "ethereum", bad)
    assert seen == []


@pytest.mark.parametrize("network,address", [
    ("ethereum", POOL),
    ("bob_network", TOKEN),
    ("solana", "So11111111111111111111111111111111111111112"),
    ("sui", "0x0000000000000000000000000000000000000000000000000000000000000002::sui::SUI"),
    ("ton", "EQA-X_yo3fzzbDbJ_0bzFWKqtRuZFIRa1sJsveZJ1YpViO3r"),
])
def test_real_ids_reach_the_path_unchanged(network, address):
    seen = []
    client, patched = _recording_client(seen)
    with patched:
        with pytest.raises(_Sent):
            client.tokens.get_details(network, address)
        with pytest.raises(_Sent):
            client.pools.get_details(network, address)
    assert seen == [
        f"/networks/{network}/tokens/{address}",
        f"/networks/{network}/pools/{address}",
    ]

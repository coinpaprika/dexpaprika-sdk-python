"""Offline check that the search filters send only keys the API accepts.

From 23 November 2026 the API answers 400 to a query key a route does not
accept (until then it ignores it, so a misspelled filter looks like an
unfiltered page). Each test sets every argument of a filter method and
compares the keys that reach the request with the route's accepted keys, as
the API defines them (dexpaprika-go internal/doc/all/static/api-rest.yml,
16 Nov 2026). No network.
"""

import unittest
from unittest import mock

from dexpaprika_sdk import DexPaprikaClient

_PRICE_CHANGE = {
    f"price_change_percentage_{w}_{b}" for w in ("5m", "1h", "6h", "24h", "48h") for b in ("min", "max")
}
_COMMON = {
    "created_after", "created_before", "cursor", "detailed", "limit", "order_by", "sort",
    "liquidity_usd_max", "liquidity_usd_min", "price_usd_max", "price_usd_min",
    "txns_24h_max", "txns_24h_min",
    "volume_usd_24h_max", "volume_usd_24h_min", "volume_usd_7d_max", "volume_usd_7d_min",
    "volume_usd_30d_max", "volume_usd_30d_min",
}
POOL_SEARCH_KEYS = _COMMON | _PRICE_CHANGE | {"dex_name", "token_address"}
TOKEN_SEARCH_KEYS = _COMMON | {
    "fdv_usd_max", "fdv_usd_min", "price_change_percentage_24h_max", "price_change_percentage_24h_min",
}


class _Stop(Exception):
    pass


def _sent_keys(api, call):
    calls = []

    def fake_get(path, params=None, **kwargs):
        calls.append({k: v for k, v in (params or {}).items() if v is not None})
        raise _Stop()

    with mock.patch.object(api, "_get", side_effect=fake_get):
        try:
            call()
        except _Stop:
            pass
    return calls[0]


class TestSearchQueryKeys(unittest.TestCase):
    def setUp(self):
        self.client = DexPaprikaClient()

    def test_tokens_filter_sends_only_accepted_keys(self):
        params = _sent_keys(self.client.tokens, lambda: self.client.tokens.filter(
            "ethereum", page=2, limit=5, sort_by="volume_usd_24h", sort_dir="asc",
            volume_24h_min=1, volume_24h_max=2, liquidity_usd_min=1, fdv_min=1, fdv_max=2,
            txns_24h_min=1, created_after="-1d", created_before="-1h", cursor="c",
            price_change_percentage_24h_min=1, price_change_percentage_24h_max=2,
        ))
        self.assertEqual(sorted(set(params) - TOKEN_SEARCH_KEYS), [])
        self.assertEqual(params["fdv_usd_min"], 1)
        self.assertEqual(params["fdv_usd_max"], 2)

    def test_pools_filter_sends_only_accepted_keys(self):
        windows = {f"price_change_percentage_{w}_{b}": 1 for w in ("5m", "1h", "6h", "24h", "48h") for b in ("min", "max")}
        params = _sent_keys(self.client.pools, lambda: self.client.pools.filter(
            "ethereum", page=2, limit=5, sort_by="volume_usd_24h", sort_dir="asc",
            volume_24h_min=1, volume_24h_max=2, volume_7d_min=1, volume_7d_max=2,
            liquidity_usd_min=1, liquidity_usd_max=2, txns_24h_min=1,
            created_after="-1d", created_before="-1h", cursor="c", **windows,
        ))
        self.assertEqual(sorted(set(params) - POOL_SEARCH_KEYS), [])


if __name__ == "__main__":
    unittest.main()

"""Offline checks that relative time filters reach the query unchanged.

The API accepts a relative offset (-1h, -24h, -7d), RFC3339 or YYYY-MM-DD on
transactions from/to and search created_after/created_before since
2026-09-28, next to Unix seconds. These tests stop at the request boundary,
so they need no network.
"""

import unittest
from unittest import mock

from dexpaprika_sdk import DexPaprikaClient

POOL = "0x88e6a0c2ddd26feeb64f039a2c41296fcb3f5640"


class _Stop(Exception):
    """Raised by the patched _get once it has recorded the request."""


def _capture(api):
    calls = []

    def fake_get(path, params=None, **kwargs):
        calls.append((path, dict(params or {})))
        raise _Stop()

    return calls, mock.patch.object(api, "_get", side_effect=fake_get)


class TestRelativeTimeFilters(unittest.TestCase):
    def setUp(self):
        self.client = DexPaprikaClient()

    def test_transactions_pass_relative_and_numeric_from_to(self):
        calls, patch = _capture(self.client.pools)
        with patch, self.assertRaises(_Stop):
            self.client.pools.get_transactions("ethereum", POOL, from_timestamp="-1h", to_timestamp=1790000000)
        path, params = calls[0]
        self.assertEqual(path, f"/networks/ethereum/pools/{POOL}/transactions")
        self.assertEqual(params["from"], "-1h")
        self.assertEqual(params["to"], 1790000000)

    def test_pools_filter_passes_relative_created_after(self):
        calls, patch = _capture(self.client.pools)
        with patch, self.assertRaises(_Stop):
            self.client.pools.filter("ethereum", created_after="-24h", created_before="-1h")
        _, params = calls[0]
        self.assertEqual(params["created_after"], "-24h")
        self.assertEqual(params["created_before"], "-1h")

    def test_tokens_filter_passes_relative_created_after(self):
        calls, patch = _capture(self.client.tokens)
        with patch, self.assertRaises(_Stop):
            self.client.tokens.filter("ethereum", created_after="-7d")
        _, params = calls[0]
        self.assertEqual(params["created_after"], "-7d")


if __name__ == "__main__":
    unittest.main()

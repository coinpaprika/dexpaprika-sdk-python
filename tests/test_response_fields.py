"""Offline checks that response models keep the fields the API sends.

Pydantic drops unknown keys, so a field missing from a model disappears
without an error. The payloads below are real responses captured on
2026-09-28 (ethereum USDC/WETH 0.05% pool, one row, and a two-token
multi-price call). The tests patch _get, so they need no network.
"""

import unittest
from unittest import mock

from dexpaprika_sdk import DexPaprikaClient

POOL = "0x88e6a0c2ddd26feeb64f039a2c41296fcb3f5640"
WETH = "0xc02aaa39b223fe8d0a0e5c4f27ead9083c756cc2"
USDC = "0xa0b86991c6218b36c1d19d4a2e9eb0ce3606eb48"

TRANSACTIONS = {
    "transactions": [
        {
            "id": "0xeb55ee41a97e3f8a23e57dd25734989c84ceabcb8ff413187e634ef219512816",
            "log_index": 27,
            "transaction_index": 0,
            "factory_id": "0x1f98431c8ad98523631ae4a59f267346ea31f984",
            "pool_id": POOL,
            "chain": "ethereum",
            "sender": "0xbdb3ba9ffe392549e1f8658dd2630c141fdf47b6",
            "recipient": "0xbdb3ba9ffe392549e1f8658dd2630c141fdf47b6",
            "token_0": WETH,
            "token_0_symbol": "WETH",
            "token_1": USDC,
            "token_1_symbol": "USDC",
            "amount_0": 4272800710322643723,
            "amount_1": -11474293823,
            "volume_0": 4.2728007103226435,
            "volume_1": 11474.293823,
            "price_0": 2684.2796155486812,
            "price_1": 0.0003725394307685023,
            "price_0_usd": 2684.3686221201683,
            "price_1_usd": 0.9996980008841365,
            "created_at_block_number": 26076150,
            "created_at_block_hash": "0x3ff6fd5f4c3a06bcfeb75627d1a38f363c60b334c0bf3fc4f3d03bea5fb41722",
            "created_at": "2026-09-28T13:07:35Z",
            "canonical_chain": True,
        }
    ],
    "page_info": {"limit": 1, "page": 0, "total_items": 1, "total_pages": 1},
}

MULTI_PRICES = [
    {"chain": "ethereum", "id": WETH, "price_usd": 2683.9827121537683, "last_updated": "2026-09-28T13:07:30Z"},
    {"chain": "ethereum", "id": USDC, "price_usd": 0.9999892971266823, "last_updated": "2026-09-28T13:07:30Z"},
]


class TestTransactionFields(unittest.TestCase):
    def setUp(self):
        client = DexPaprikaClient()
        with mock.patch.object(client.pools, "_get", return_value=TRANSACTIONS):
            self.tx = client.pools.get_transactions("ethereum", POOL, limit=1).transactions[0]

    def test_time_and_chain(self):
        self.assertEqual(self.tx.created_at, "2026-09-28T13:07:35Z")
        self.assertEqual(self.tx.created_at_block_hash, TRANSACTIONS["transactions"][0]["created_at_block_hash"])
        self.assertEqual(self.tx.chain, "ethereum")
        self.assertEqual(self.tx.factory_id, "0x1f98431c8ad98523631ae4a59f267346ea31f984")
        self.assertIs(self.tx.canonical_chain, True)

    def test_symbols_volumes_and_prices(self):
        self.assertEqual((self.tx.token_0_symbol, self.tx.token_1_symbol), ("WETH", "USDC"))
        self.assertAlmostEqual(self.tx.volume_0, 4.2728007103226435)
        self.assertAlmostEqual(self.tx.volume_1, 11474.293823)
        self.assertAlmostEqual(self.tx.price_0, 2684.2796155486812)
        self.assertAlmostEqual(self.tx.price_1, 0.0003725394307685023)
        self.assertAlmostEqual(self.tx.price_0_usd, 2684.3686221201683)
        self.assertAlmostEqual(self.tx.price_1_usd, 0.9996980008841365)

    def test_raw_amounts_keep_full_precision(self):
        self.assertEqual(self.tx.amount_0, 4272800710322643723)
        self.assertEqual(self.tx.amount_1, -11474293823)

    def test_new_fields_are_optional(self):
        row = {k: v for k, v in TRANSACTIONS["transactions"][0].items()
               if k in ("id", "log_index", "transaction_index", "pool_id", "sender", "recipient",
                        "token_0", "token_1", "amount_0", "amount_1", "created_at_block_number")}
        client = DexPaprikaClient()
        payload = {"transactions": [row], "page_info": TRANSACTIONS["page_info"]}
        with mock.patch.object(client.pools, "_get", return_value=payload):
            tx = client.pools.get_transactions("ethereum", POOL, limit=1).transactions[0]
        self.assertIsNone(tx.created_at)
        self.assertIsNone(tx.price_0_usd)


class TestMultiPriceFields(unittest.TestCase):
    def test_last_updated(self):
        client = DexPaprikaClient()
        with mock.patch.object(client.tokens, "_get", return_value=MULTI_PRICES):
            prices = client.tokens.get_multi_prices("ethereum", [WETH, USDC])
        self.assertEqual([p.last_updated for p in prices], ["2026-09-28T13:07:30Z"] * 2)


if __name__ == "__main__":
    unittest.main()

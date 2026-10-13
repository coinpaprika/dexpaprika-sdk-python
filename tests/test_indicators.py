#!/usr/bin/env python3
"""Tests for pools.get_indicator() and tokens.get_indicator(), GET
/networks/{network}/pools/{pool_address}/indicators and
GET /networks/{network}/tokens/{token_address}/indicators.

Mirrors test_token_ohlcv.py's structure: one class for the query sent to the
transport (path, and that only parameters the caller set are included),
one for validation, one for parsing each indicator's response shape, and one
for error surfacing (400 for a parameter that belongs to another indicator,
403 plan_required on the token endpoint).

Response bodies below are taken from live samples captured 2026-10-13.
"""

import json
import unittest
from unittest.mock import patch

import requests
from requests.exceptions import HTTPError

from dexpaprika_sdk import DexPaprikaClient
from dexpaprika_sdk.models import IndicatorResponse

NETWORK = "ethereum"
POOL = "0x88e6a0c2ddd26feeb64f039a2c41296fcb3f5640"
TOKEN = "0xa0b86991c6218b36c1d19d4a2e9eb0ce3606eb48"  # USDC

# Live sample, samples/pool-rsi.json.
LIVE_POOL_RSI_BODY = {
    "network": "ethereum",
    "pool_address": POOL,
    "indicator": "rsi",
    "interval": "1h",
    "parameters": {"period": 14},
    "data": [
        {"timestamp": "2026-10-13T06:00:00Z", "value": 54.38666301724629},
        {"timestamp": "2026-10-13T07:00:00Z", "value": 53.184343874602874},
        {"timestamp": "2026-10-13T08:00:00Z", "value": 51.087952277014196},
    ],
    "has_next_page": True,
    "next_cursor": "1791882000",
}

# Live sample, samples/pool-macd.json.
LIVE_POOL_MACD_BODY = {
    "network": "ethereum",
    "pool_address": POOL,
    "indicator": "macd",
    "interval": "1h",
    "parameters": {"fast_period": 12, "signal_period": 9, "slow_period": 26},
    "data": [
        {
            "timestamp": "2026-10-13T06:00:00Z",
            "macd": -11.534946379135818,
            "signal": -22.75562121248413,
            "histogram": 11.220674833348312,
        },
        {
            "timestamp": "2026-10-13T07:00:00Z",
            "macd": -8.78613090817089,
            "signal": -19.96172315162148,
            "histogram": 11.175592243450591,
        },
    ],
    "has_next_page": True,
    "next_cursor": "1791882000",
}


class TestPoolIndicatorRequest(unittest.TestCase):
    """The path and query sent to the transport, for the pool endpoint."""

    def setUp(self):
        self.client = DexPaprikaClient()

    def _patched_get(self, body=None):
        return patch.object(
            self.client.pools, "_get",
            return_value=json.loads(json.dumps(body if body is not None else LIVE_POOL_RSI_BODY)),
        )

    def test_targets_pool_indicators_path(self):
        with self._patched_get() as mock_get:
            self.client.pools.get_indicator(NETWORK, POOL, indicator="rsi")

        endpoint = mock_get.call_args.args[0]
        self.assertEqual(endpoint, f"/networks/{NETWORK}/pools/{POOL}/indicators")

    def test_indicator_is_always_sent(self):
        with self._patched_get() as mock_get:
            self.client.pools.get_indicator(NETWORK, POOL, indicator="rsi")

        params = mock_get.call_args.kwargs["params"]
        self.assertEqual(params["indicator"], "rsi")
        self.assertEqual(params, {"indicator": "rsi"})

    def test_only_params_the_caller_set_are_sent(self):
        """No defaults are filled in for interval, period, limit, etc."""
        with self._patched_get() as mock_get:
            self.client.pools.get_indicator(NETWORK, POOL, indicator="rsi", period=20)

        params = mock_get.call_args.kwargs["params"]
        self.assertEqual(params, {"indicator": "rsi", "period": 20})
        self.assertNotIn("interval", params)
        self.assertNotIn("limit", params)
        self.assertNotIn("start", params)
        self.assertNotIn("end", params)
        self.assertNotIn("cursor", params)

    def test_macd_params_sent_without_period(self):
        with self._patched_get(LIVE_POOL_MACD_BODY) as mock_get:
            self.client.pools.get_indicator(
                NETWORK, POOL, indicator="macd",
                interval="1h", fast_period=12, slow_period=26, signal_period=9,
            )

        params = mock_get.call_args.kwargs["params"]
        self.assertEqual(
            params,
            {
                "indicator": "macd",
                "interval": "1h",
                "fast_period": 12,
                "slow_period": 26,
                "signal_period": 9,
            },
        )
        self.assertNotIn("period", params)

    def test_bbands_std_dev_sent(self):
        with self._patched_get() as mock_get:
            self.client.pools.get_indicator(
                NETWORK, POOL, indicator="bbands", period=20, std_dev=2.5,
            )

        params = mock_get.call_args.kwargs["params"]
        self.assertEqual(params["std_dev"], 2.5)
        self.assertEqual(params["period"], 20)

    def test_start_end_limit_cursor_carried_through(self):
        with self._patched_get() as mock_get:
            self.client.pools.get_indicator(
                NETWORK, POOL, indicator="ema", start="-6h", end="-1h", limit=50,
            )

        params = mock_get.call_args.kwargs["params"]
        self.assertEqual(params["start"], "-6h")
        self.assertEqual(params["end"], "-1h")
        self.assertEqual(params["limit"], 50)

    def test_cursor_carried_through_alone(self):
        with self._patched_get() as mock_get:
            self.client.pools.get_indicator(
                NETWORK, POOL, indicator="rsi", cursor="1791882000",
            )

        params = mock_get.call_args.kwargs["params"]
        self.assertEqual(params["cursor"], "1791882000")
        self.assertNotIn("start", params)


class TestTokenIndicatorRequest(unittest.TestCase):
    """The path and query sent to the transport, for the token endpoint."""

    def setUp(self):
        self.client = DexPaprikaClient()

    def _patched_get(self, body=None):
        return patch.object(
            self.client.tokens, "_get",
            return_value=json.loads(json.dumps(
                body if body is not None else {**LIVE_POOL_RSI_BODY, "pool_address": None, "token_address": TOKEN}
            )),
        )

    def test_targets_token_indicators_path(self):
        with self._patched_get() as mock_get:
            self.client.tokens.get_indicator(NETWORK, TOKEN, indicator="rsi")

        endpoint = mock_get.call_args.args[0]
        self.assertEqual(endpoint, f"/networks/{NETWORK}/tokens/{TOKEN}/indicators")

    def test_only_params_the_caller_set_are_sent(self):
        with self._patched_get() as mock_get:
            self.client.tokens.get_indicator(NETWORK, TOKEN, indicator="ema", period=20)

        params = mock_get.call_args.kwargs["params"]
        self.assertEqual(params, {"indicator": "ema", "period": 20})


class TestIndicatorValidation(unittest.TestCase):
    """Same validation shape as pools.get_ohlcv() / tokens.get_ohlcv()."""

    def setUp(self):
        self.client = DexPaprikaClient()

    def test_required_parameters(self):
        with self.assertRaises(ValueError) as context:
            self.client.pools.get_indicator(network_id="", pool_address=POOL, indicator="rsi")
        self.assertIn("network_id is required", str(context.exception))

        with self.assertRaises(ValueError) as context:
            self.client.pools.get_indicator(network_id=NETWORK, pool_address="", indicator="rsi")
        self.assertIn("pool_address is required", str(context.exception))

        with self.assertRaises(ValueError) as context:
            self.client.pools.get_indicator(network_id=NETWORK, pool_address=POOL, indicator="")
        self.assertIn("indicator is required", str(context.exception))

    def test_indicator_enum_validation(self):
        with self.assertRaises(ValueError) as context:
            self.client.pools.get_indicator(NETWORK, POOL, indicator="sma")
        self.assertIn("indicator must be one of:", str(context.exception))

    def test_interval_enum_validation(self):
        with self.assertRaises(ValueError) as context:
            self.client.pools.get_indicator(NETWORK, POOL, indicator="rsi", interval="2h")
        self.assertIn("interval must be one of:", str(context.exception))

    def test_1d_is_a_valid_interval(self):
        """Unlike get_ohlcv(), the indicators endpoint accepts "1d" as an
        alias for "24h"."""
        with patch.object(
            self.client.pools, "_get", return_value=json.loads(json.dumps(LIVE_POOL_RSI_BODY)),
        ) as mock_get:
            self.client.pools.get_indicator(NETWORK, POOL, indicator="rsi", interval="1d")
        self.assertEqual(mock_get.call_args.kwargs["params"]["interval"], "1d")

    def test_limit_range_validation(self):
        with self.assertRaises(ValueError) as context:
            self.client.pools.get_indicator(NETWORK, POOL, indicator="rsi", limit=0)
        self.assertIn("limit must be at least 1", str(context.exception))

        with self.assertRaises(ValueError) as context:
            self.client.pools.get_indicator(NETWORK, POOL, indicator="rsi", limit=1001)
        self.assertIn("limit must be at most 1000", str(context.exception))

    def test_period_range_validation(self):
        with self.assertRaises(ValueError) as context:
            self.client.pools.get_indicator(NETWORK, POOL, indicator="rsi", period=0)
        self.assertIn("period must be at least 1", str(context.exception))

        with self.assertRaises(ValueError) as context:
            self.client.pools.get_indicator(NETWORK, POOL, indicator="rsi", period=201)
        self.assertIn("period must be at most 200", str(context.exception))

    def test_macd_period_range_validation(self):
        with self.assertRaises(ValueError) as context:
            self.client.pools.get_indicator(NETWORK, POOL, indicator="macd", fast_period=0)
        self.assertIn("fast_period must be at least 1", str(context.exception))

        with self.assertRaises(ValueError) as context:
            self.client.pools.get_indicator(NETWORK, POOL, indicator="macd", slow_period=1)
        self.assertIn("slow_period must be at least 2", str(context.exception))

    def test_std_dev_must_be_positive(self):
        with self.assertRaises(ValueError) as context:
            self.client.pools.get_indicator(NETWORK, POOL, indicator="bbands", std_dev=0)
        self.assertIn("std_dev must be greater than 0", str(context.exception))

        with self.assertRaises(ValueError) as context:
            self.client.pools.get_indicator(NETWORK, POOL, indicator="bbands", std_dev=-1)
        self.assertIn("std_dev must be greater than 0", str(context.exception))

        with self.assertRaises(ValueError) as context:
            self.client.pools.get_indicator(NETWORK, POOL, indicator="bbands", std_dev=10.5)
        self.assertIn("std_dev must be at most 10", str(context.exception))

    def test_cursor_cannot_combine_with_start(self):
        with self.assertRaises(ValueError) as context:
            self.client.pools.get_indicator(
                NETWORK, POOL, indicator="rsi", cursor="1791882000", start="-6h",
            )
        self.assertIn("cursor cannot be combined with start", str(context.exception))

    def test_same_validation_applies_to_tokens(self):
        with self.assertRaises(ValueError) as context:
            self.client.tokens.get_indicator(network_id="", token_address=TOKEN, indicator="rsi")
        self.assertIn("network_id is required", str(context.exception))

        with self.assertRaises(ValueError) as context:
            self.client.tokens.get_indicator(NETWORK, TOKEN, indicator="sma")
        self.assertIn("indicator must be one of:", str(context.exception))


class TestIndicatorResponseParsing(unittest.TestCase):
    """rsi and macd response shapes parse into IndicatorResponse."""

    def setUp(self):
        self.client = DexPaprikaClient()

    def test_rsi_shape_parses(self):
        with patch.object(
            self.client.pools, "_get", return_value=json.loads(json.dumps(LIVE_POOL_RSI_BODY)),
        ):
            result = self.client.pools.get_indicator(NETWORK, POOL, indicator="rsi", interval="1h")

        self.assertIsInstance(result, IndicatorResponse)
        self.assertEqual(result.network, "ethereum")
        self.assertEqual(result.pool_address, POOL)
        self.assertIsNone(result.token_address)
        self.assertEqual(result.indicator, "rsi")
        self.assertEqual(result.interval, "1h")
        self.assertEqual(result.parameters, {"period": 14})
        self.assertTrue(result.has_next_page)
        self.assertEqual(result.next_cursor, "1791882000")
        self.assertEqual(len(result.data), 3)
        first = result.data[0]
        self.assertEqual(first.timestamp, "2026-10-13T06:00:00Z")
        self.assertAlmostEqual(first.value, 54.38666301724629)
        self.assertIsNone(first.macd)
        self.assertIsNone(first.upper)

    def test_macd_shape_parses(self):
        with patch.object(
            self.client.pools, "_get", return_value=json.loads(json.dumps(LIVE_POOL_MACD_BODY)),
        ):
            result = self.client.pools.get_indicator(NETWORK, POOL, indicator="macd", interval="1h")

        self.assertEqual(result.indicator, "macd")
        self.assertEqual(result.parameters, {"fast_period": 12, "signal_period": 9, "slow_period": 26})
        first = result.data[0]
        self.assertAlmostEqual(first.macd, -11.534946379135818)
        self.assertAlmostEqual(first.signal, -22.75562121248413)
        self.assertAlmostEqual(first.histogram, 11.220674833348312)
        self.assertIsNone(first.value)

    def test_bbands_shape_parses(self):
        body = {
            "network": "ethereum",
            "pool_address": POOL,
            "indicator": "bbands",
            "interval": "1h",
            "parameters": {"period": 20, "std_dev": 2},
            "data": [
                {"timestamp": "2026-10-13T06:00:00Z", "upper": 2600.1, "middle": 2505.3, "lower": 2410.5},
            ],
            "has_next_page": False,
            "next_cursor": "",
        }
        with patch.object(self.client.pools, "_get", return_value=body):
            result = self.client.pools.get_indicator(NETWORK, POOL, indicator="bbands")

        first = result.data[0]
        self.assertAlmostEqual(first.upper, 2600.1)
        self.assertAlmostEqual(first.middle, 2505.3)
        self.assertAlmostEqual(first.lower, 2410.5)
        self.assertFalse(result.has_next_page)

    def test_token_response_carries_token_address_not_pool_address(self):
        body = {**LIVE_POOL_RSI_BODY, "pool_address": None, "token_address": TOKEN}
        with patch.object(self.client.tokens, "_get", return_value=body):
            result = self.client.tokens.get_indicator(NETWORK, TOKEN, indicator="rsi")

        self.assertEqual(result.token_address, TOKEN)
        self.assertIsNone(result.pool_address)


class TestIndicatorErrorSurfacing(unittest.TestCase):
    """A parameter refused for an indicator, and a 403 plan_required, must
    surface through the SDK's existing error type with the API's message."""

    def setUp(self):
        self.client = DexPaprikaClient()

    @staticmethod
    def _error_response(status_code, body):
        response = requests.Response()
        response.status_code = status_code
        response._content = json.dumps(body).encode("utf-8")
        return response

    def test_400_wrong_param_for_indicator_is_surfaced(self):
        body = {
            "error": "invalid_param",
            "message": "invalid query parameters: fast_period (unsupported parameter for rsi)",
            "param": "fast_period",
        }
        with patch('requests.Session.request') as mock_request:
            mock_request.return_value = self._error_response(400, body)

            with self.assertRaises(HTTPError) as ctx:
                self.client.pools.get_indicator(NETWORK, POOL, indicator="rsi", fast_period=3)

            self.assertIn("400 Client Error", str(ctx.exception))
            self.assertIn("unsupported parameter for rsi", str(ctx.exception))
            self.assertEqual(ctx.exception.response.status_code, 400)
            # A bad parameter is deterministic; it must not be retried.
            self.assertEqual(mock_request.call_count, 1)

    def test_token_indicator_403_plan_required_is_surfaced(self):
        body = {
            "error": "plan_required",
            "message": "token indicators require a Dev, Pro or Enterprise plan",
            "required_tier": "dev",
        }
        with patch('requests.Session.request') as mock_request:
            mock_request.return_value = self._error_response(403, body)

            with self.assertRaises(HTTPError) as ctx:
                self.client.tokens.get_indicator(NETWORK, TOKEN, indicator="rsi")

            self.assertIn("403 Client Error", str(ctx.exception))
            self.assertIn("require a Dev, Pro or Enterprise plan", str(ctx.exception))
            self.assertEqual(ctx.exception.response.status_code, 403)
            self.assertEqual(mock_request.call_count, 1)

    def test_404_not_found_is_surfaced(self):
        body = {"error": "not_found", "message": "pool not found", "resource": "pool"}
        with patch('requests.Session.request') as mock_request:
            mock_request.return_value = self._error_response(404, body)

            with self.assertRaises(HTTPError) as ctx:
                self.client.pools.get_indicator(NETWORK, "0xdeadbeef", indicator="rsi")

            self.assertIn("404 Client Error", str(ctx.exception))
            self.assertIn("pool not found", str(ctx.exception))


if __name__ == "__main__":
    unittest.main()

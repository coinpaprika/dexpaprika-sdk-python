#!/usr/bin/env python3
"""Tests for tokens.get_ohlcv(), GET /networks/{network}/tokens/{token_address}/ohlcv.

Mirrors the existing pools.get_ohlcv() coverage (test_validation.py's limit and
interval checks, test_features.py's error-message surfacing) plus checks
specific to the token endpoint: the exact path and query sent, and that no
`inversed` parameter is ever included, since there is no second token to
invert against on this endpoint.
"""

import json
import unittest
from unittest.mock import patch

import requests
from requests.exceptions import HTTPError

from dexpaprika_sdk import DexPaprikaClient
from dexpaprika_sdk.models import OHLCVRecord

NETWORK = "ethereum"
TOKEN = "0xa0b86991c6218b36c1d19d4a2e9eb0ce3606eb48"  # USDC

# Shape matches pools.get_ohlcv()'s response: a bare JSON array of candles.
LIVE_TOKEN_OHLCV_BODY = [
    {
        "time_open": "2026-09-28T00:00:00Z",
        "time_close": "2026-09-28T01:00:00Z",
        "open": 1.0001,
        "high": 1.0006,
        "low": 0.9998,
        "close": 1.0002,
        "volume": 48213899,
    },
    {
        "time_open": "2026-09-28T01:00:00Z",
        "time_close": "2026-09-28T02:00:00Z",
        "open": 1.0002,
        "high": 1.0007,
        "low": 0.9999,
        "close": 1.0003,
        "volume": 39122011,
    },
]


class TestTokenOhlcvRequest(unittest.TestCase):
    """The path and query sent to the transport."""

    def setUp(self):
        self.client = DexPaprikaClient()

    def _patched_get(self):
        return patch.object(
            self.client.tokens, "_get",
            return_value=json.loads(json.dumps(LIVE_TOKEN_OHLCV_BODY)),
        )

    def test_targets_token_ohlcv_path(self):
        with self._patched_get() as mock_get:
            self.client.tokens.get_ohlcv(NETWORK, TOKEN, start="-24h")

        endpoint = mock_get.call_args.args[0]
        self.assertEqual(endpoint, f"/networks/{NETWORK}/tokens/{TOKEN}/ohlcv")

    def test_query_carries_start_end_limit_interval(self):
        with self._patched_get() as mock_get:
            self.client.tokens.get_ohlcv(
                NETWORK, TOKEN, start="-7d", end="-1h", limit=50, interval="1h",
            )

        params = mock_get.call_args.kwargs["params"]
        self.assertEqual(params["start"], "-7d")
        self.assertEqual(params["end"], "-1h")
        self.assertEqual(params["limit"], 50)
        self.assertEqual(params["interval"], "1h")

    def test_no_inversed_parameter_is_ever_sent(self):
        """Unlike pools.get_ohlcv(), there is no inversed to flip."""
        with self._patched_get() as mock_get:
            self.client.tokens.get_ohlcv(NETWORK, TOKEN, start="-24h")

        params = mock_get.call_args.kwargs["params"]
        self.assertNotIn("inversed", params)
        # And the method itself takes no such argument.
        with self.assertRaises(TypeError):
            self.client.tokens.get_ohlcv(NETWORK, TOKEN, start="-24h", inversed=True)

    def test_end_omitted_when_not_given(self):
        with self._patched_get() as mock_get:
            self.client.tokens.get_ohlcv(NETWORK, TOKEN, start="-24h")

        params = mock_get.call_args.kwargs["params"]
        self.assertNotIn("end", params)

    def test_default_limit_and_interval_match_server_defaults(self):
        with self._patched_get() as mock_get:
            self.client.tokens.get_ohlcv(NETWORK, TOKEN, start="-24h")

        params = mock_get.call_args.kwargs["params"]
        self.assertEqual(params["limit"], 10)
        self.assertEqual(params["interval"], "24h")

    def test_response_parses_into_ohlcv_records(self):
        with self._patched_get():
            records = self.client.tokens.get_ohlcv(NETWORK, TOKEN, start="-24h")

        self.assertEqual(len(records), 2)
        self.assertIsInstance(records[0], OHLCVRecord)
        self.assertEqual(records[0].time_open, "2026-09-28T00:00:00Z")
        self.assertEqual(records[0].time_close, "2026-09-28T01:00:00Z")
        self.assertEqual(records[0].open, 1.0001)
        self.assertEqual(records[0].high, 1.0006)
        self.assertEqual(records[0].low, 0.9998)
        self.assertEqual(records[0].close, 1.0002)
        self.assertEqual(records[0].volume, 48213899)


class TestTokenOhlcvValidation(unittest.TestCase):
    """Same limit and interval validation as pools.get_ohlcv()."""

    def setUp(self):
        self.client = DexPaprikaClient()

    def test_required_parameters(self):
        with self.assertRaises(ValueError) as context:
            self.client.tokens.get_ohlcv(network_id="", token_address=TOKEN, start="-24h")
        self.assertIn("network_id is required", str(context.exception))

        with self.assertRaises(ValueError) as context:
            self.client.tokens.get_ohlcv(network_id=NETWORK, token_address="", start="-24h")
        self.assertIn("token_address is required", str(context.exception))

        with self.assertRaises(ValueError) as context:
            self.client.tokens.get_ohlcv(network_id=NETWORK, token_address=TOKEN, start="")
        self.assertIn("start is required", str(context.exception))

    def test_interval_enum_validation(self):
        with self.assertRaises(ValueError) as context:
            self.client.tokens.get_ohlcv(
                network_id=NETWORK, token_address=TOKEN, start="-24h", interval="invalid",
            )
        self.assertIn("interval must be one of:", str(context.exception))

    def test_limit_range_validation(self):
        with self.assertRaises(ValueError) as context:
            self.client.tokens.get_ohlcv(
                network_id=NETWORK, token_address=TOKEN, start="-24h", limit=0,
            )
        self.assertIn("limit must be at least 1", str(context.exception))

        # Tops out at 1000, same as pools.get_ohlcv().
        with self.assertRaises(ValueError) as context:
            self.client.tokens.get_ohlcv(
                network_id=NETWORK, token_address=TOKEN, start="-24h", limit=1001,
            )
        self.assertIn("limit must be at most 1000", str(context.exception))

    def test_limit_1000_is_accepted(self):
        with patch.object(
            self.client.tokens, "_get",
            return_value=json.loads(json.dumps(LIVE_TOKEN_OHLCV_BODY)),
        ) as mock_get:
            self.client.tokens.get_ohlcv(
                network_id=NETWORK, token_address=TOKEN, start="-24h", limit=1000,
            )
        self.assertEqual(mock_get.call_args.kwargs["params"]["limit"], 1000)


class TestTokenOhlcvErrorSurfacing(unittest.TestCase):
    """A 403 on this endpoint must carry the API's plan-requirement message."""

    def setUp(self):
        self.client = DexPaprikaClient()

    @staticmethod
    def _error_response(status_code, body):
        response = requests.Response()
        response.status_code = status_code
        response._content = json.dumps(body).encode("utf-8")
        return response

    def test_403_message_is_surfaced(self):
        body = {"message": "this endpoint requires a Dev or Pro plan"}
        with patch('requests.Session.request') as mock_request:
            mock_request.return_value = self._error_response(403, body)

            with self.assertRaises(HTTPError) as ctx:
                self.client.tokens.get_ohlcv(NETWORK, TOKEN, start="-24h")

            self.assertIn("403 Client Error", str(ctx.exception))
            self.assertIn("this endpoint requires a Dev or Pro plan", str(ctx.exception))
            self.assertEqual(ctx.exception.response.status_code, 403)
            # A plan limit is deterministic; it must not be retried.
            self.assertEqual(mock_request.call_count, 1)


if __name__ == "__main__":
    unittest.main()


# A real 1m UNI candle from api-pro on 2026-09-29. Its USD volume rounded down
# to 0, so the API left the field out; 0.12.0 raised ValidationError on it.
CANDLE_WITHOUT_VOLUME = {
    "time_open": "2026-09-29T09:13:00Z",
    "time_close": "2026-09-29T09:14:00Z",
    "open": 8.977335891233913,
    "high": 8.977335891233913,
    "low": 8.977335891233913,
    "close": 8.977335891233913,
}


class TestCandleWithoutVolume(unittest.TestCase):
    """A candle with no `volume` key parses, with volume 0."""

    def test_model_defaults_volume_to_zero(self):
        self.assertEqual(OHLCVRecord(**CANDLE_WITHOUT_VOLUME).volume, 0)

    def test_get_ohlcv_parses_a_series_with_a_gap_in_volume(self):
        client = DexPaprikaClient()
        body = [LIVE_TOKEN_OHLCV_BODY[0], CANDLE_WITHOUT_VOLUME]
        with patch.object(client.tokens, "_get", return_value=body):
            candles = client.tokens.get_ohlcv(NETWORK, TOKEN, start="-2h", interval="1m", limit=2)
        self.assertEqual([c.volume for c in candles], [48213899, 0])

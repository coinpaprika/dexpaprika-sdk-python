#!/usr/bin/env python3
"""
Test script to verify caching and retry behavior in the DexPaprika SDK.
"""

import unittest
import time
import json
from datetime import timedelta
from unittest.mock import patch, MagicMock
import requests
from requests.exceptions import ConnectionError, Timeout, HTTPError

from dexpaprika_sdk import DexPaprikaClient
from dexpaprika_sdk.exceptions import DeprecatedEndpointError, DexPaprikaError


class TestCachingBehavior(unittest.TestCase):
    """Test suite for caching functionality."""
    
    def setUp(self):
        """Set up test environment."""
        self.client = DexPaprikaClient()
    
    def test_basic_caching(self):
        """Test that responses are cached and reused."""
        # Make first request
        with patch('requests.Session.request') as mock_request:
            mock_response = MagicMock()
            mock_response.content = b'{"test": "data"}'
            mock_response.json.return_value = {"test": "data"}
            mock_request.return_value = mock_response
            
            # First request should call the API
            self.client.networks._get("/test_endpoint")
            self.assertEqual(mock_request.call_count, 1)
            
            # Second request should use the cache
            self.client.networks._get("/test_endpoint")
            self.assertEqual(mock_request.call_count, 1)
    
    def test_cache_with_params(self):
        """Test that parameterized requests are cached correctly."""
        # Make first request with params
        with patch('requests.Session.request') as mock_request:
            mock_response = MagicMock()
            mock_response.content = b'{"test": "data"}'
            mock_response.json.return_value = {"test": "data"}
            mock_request.return_value = mock_response
            
            # First request with params
            self.client.networks._get("/test_endpoint", params={"param1": "value1"})
            self.assertEqual(mock_request.call_count, 1)
            
            # Same request with same params
            self.client.networks._get("/test_endpoint", params={"param1": "value1"})
            self.assertEqual(mock_request.call_count, 1)
            
            # Different params should trigger a new request
            self.client.networks._get("/test_endpoint", params={"param1": "value2"})
            self.assertEqual(mock_request.call_count, 2)
    
    def test_skip_cache(self):
        """Test that skip_cache works as expected."""
        with patch('requests.Session.request') as mock_request:
            mock_response = MagicMock()
            mock_response.content = b'{"test": "data"}'
            mock_response.json.return_value = {"test": "data"}
            mock_request.return_value = mock_response
            
            # First request
            self.client.networks._get("/test_endpoint")
            self.assertEqual(mock_request.call_count, 1)
            
            # Second request with skip_cache=True
            self.client.networks._get("/test_endpoint", skip_cache=True)
            self.assertEqual(mock_request.call_count, 2)
    
    def test_clear_cache(self):
        """Test that clear_cache works as expected."""
        with patch('requests.Session.request') as mock_request:
            mock_response = MagicMock()
            mock_response.content = b'{"test": "data"}'
            mock_response.json.return_value = {"test": "data"}
            mock_request.return_value = mock_response
            
            # First request
            self.client.networks._get("/test_endpoint")
            self.assertEqual(mock_request.call_count, 1)
            
            # Clear cache
            self.client.clear_cache()
            
            # Second request after clearing cache
            self.client.networks._get("/test_endpoint")
            self.assertEqual(mock_request.call_count, 2)


class TestRetryBehavior(unittest.TestCase):
    """Test suite for retry with backoff functionality."""
    
    def setUp(self):
        """Set up test environment."""
        self.client = DexPaprikaClient(max_retries=2, backoff_times=[0.01, 0.02])
    
    def test_connection_error_retry(self):
        """Test retry on connection errors."""
        with patch('requests.Session.request') as mock_request:
            mock_request.side_effect = [
                ConnectionError("Connection refused"),
                ConnectionError("Connection refused"),
                MagicMock(content=b'{"success":true}', json=lambda: {"success": True})
            ]
            
            # This should succeed after 2 retries
            result = self.client.get("/test_endpoint")
            
            self.assertEqual(mock_request.call_count, 3)
            self.assertEqual(result, {"success": True})
    
    def test_server_error_retry(self):
        """Test retry on server errors (5xx)."""
        with patch('requests.Session.request') as mock_request:
            # Create a response with a 500 status code
            error_response = requests.Response()
            error_response.status_code = 500
            
            # Create the HTTPError from this response
            http_error = HTTPError("500 Server Error", response=error_response)
            
            mock_response = MagicMock()
            mock_response.content = b'{"success":true}'
            mock_response.json.return_value = {"success": True}
            
            # First request raises 500 error, then succeeds
            mock_request.side_effect = [
                MagicMock(raise_for_status=MagicMock(side_effect=http_error)),
                mock_response
            ]
            
            # This should succeed after 1 retry
            result = self.client.get("/test_endpoint")
            
            self.assertEqual(mock_request.call_count, 2)
            self.assertEqual(result, {"success": True})
    
    def test_no_retry_on_client_error(self):
        """Test that client errors (4xx) are not retried."""
        with patch('requests.Session.request') as mock_request:
            # Create a response with a 404 status code
            error_response = requests.Response()
            error_response.status_code = 404
            
            # Create the HTTPError from this response
            http_error = HTTPError("404 Not Found", response=error_response)
            
            # Set up the mock to return a response that will raise HTTPError
            mock_response = MagicMock()
            mock_response.raise_for_status.side_effect = http_error
            mock_request.return_value = mock_response
            
            # This should fail immediately without retrying
            with self.assertRaises(HTTPError):
                self.client.get("/test_endpoint")
            
            # Should only be called once (no retries)
            self.assertEqual(mock_request.call_count, 1)
    
    def test_max_retries_exceeded(self):
        """Test that the request fails after max retries are exceeded."""
        with patch('requests.Session.request') as mock_request:
            # All requests raise connection errors
            mock_request.side_effect = ConnectionError("Connection refused")
            
            # This should fail after max retries
            with self.assertRaises(ConnectionError):
                self.client.get("/test_endpoint")
            
            # Should be called 3 times (initial + 2 retries)
            self.assertEqual(mock_request.call_count, 3)


class TestDeprecationHandling(unittest.TestCase):
    """Test suite for the API's self-documenting deprecation hints."""

    def setUp(self):
        """Set up test environment."""
        self.client = DexPaprikaClient(max_retries=2, backoff_times=[0.01, 0.02])

    @staticmethod
    def _error_response(status_code, body):
        """Build a real requests.Response with a JSON (or raw) error body."""
        response = requests.Response()
        response.status_code = status_code
        if isinstance(body, (dict, list)):
            response._content = json.dumps(body).encode("utf-8")
        else:
            response._content = body.encode("utf-8") if isinstance(body, str) else body
        return response

    def test_replacement_raises_typed_error(self):
        """A 410 body with a replacement raises DeprecatedEndpointError."""
        body = {
            "code": 410,
            "message": "endpoint removed",
            "replacement": "/networks/:network/pools/search",
        }
        with patch('requests.Session.request') as mock_request:
            mock_request.return_value = self._error_response(410, body)

            with self.assertRaises(DeprecatedEndpointError) as ctx:
                self.client.get("/pools")

            error = ctx.exception
            # It surfaces both the API message and the replacement.
            self.assertEqual(error.replacement, "/networks/:network/pools/search")
            self.assertEqual(error.api_message, "endpoint removed")
            self.assertEqual(error.status_code, 410)
            self.assertIn("endpoint removed", str(error))
            self.assertIn(
                "Use /networks/:network/pools/search instead.", str(error)
            )
            # It is a DexPaprikaError so callers can catch the family.
            self.assertIsInstance(error, DexPaprikaError)

    def test_replacement_is_not_retried(self):
        """Deprecation hints are deterministic and must not be retried."""
        body = {"message": "endpoint removed", "replacement": "/pools/search"}
        with patch('requests.Session.request') as mock_request:
            mock_request.return_value = self._error_response(410, body)

            with self.assertRaises(DeprecatedEndpointError):
                self.client.get("/pools")

            self.assertEqual(mock_request.call_count, 1)

    def test_replacement_generic_across_status_codes(self):
        """Any error status with a replacement surfaces the typed error."""
        body = {"message": "moved", "replacement": "/tokens/search"}
        with patch('requests.Session.request') as mock_request:
            mock_request.return_value = self._error_response(400, body)

            with self.assertRaises(DeprecatedEndpointError) as ctx:
                self.client.get("/tokens/top")

            self.assertEqual(ctx.exception.replacement, "/tokens/search")
            self.assertEqual(ctx.exception.status_code, 400)

    def test_error_without_replacement_falls_back(self):
        """An error body without a replacement keeps the bare HTTPError behavior."""
        body = {"code": 410, "message": "endpoint removed"}
        with patch('requests.Session.request') as mock_request:
            mock_request.return_value = self._error_response(410, body)

            with self.assertRaises(HTTPError):
                self.client.get("/pools")

    def test_non_json_error_falls_back(self):
        """A non-JSON error body keeps the bare HTTPError behavior."""
        with patch('requests.Session.request') as mock_request:
            mock_request.return_value = self._error_response(410, "not json at all")

            with self.assertRaises(HTTPError):
                self.client.get("/pools")


# Trimmed from a live GET /networks/ethereum/pools/search?limit=2&dex_name=curve
# captured 2026-08-05. Field names are copied off the wire, not invented: there
# is no bare volume_usd and no page_info on this endpoint.
LIVE_DEX_SEARCH_BODY = {
    "results": [
        {
            "id": "0x4f493b7de8aac7d55f71853688b1f7c8f0243c85",
            "dex_id": "curve",
            "dex_name": "Curve",
            "chain": "ethereum",
            "volume_usd_24h": 15883391.558251368,
            "created_at": "2025-01-25T17:20:47Z",
            "created_at_block_number": 21702976,
            "transactions_24h": 289,
            "price_usd": 0.9995787501356217,
            "price_change_percentage_5m": None,
            "price_change_percentage_1h": 0.02422482089565938,
            "price_change_percentage_6h": 0.009802157529374174,
            "price_change_percentage_24h": 0.007018797950998323,
            "fee": None,
            "volume_usd_7d": 31781851.73428885,
            "volume_usd_30d": 136889876.39037386,
            "liquidity_usd": 7407910.088430515,
            "tokens": [
                {"id": "0xa0b86991c6218b36c1d19d4a2e9eb0ce3606eb48", "chain": "ethereum", "has_image": True},
                {"id": "0xdac17f958d2ee523a2206206994597c13d831ec7", "chain": "ethereum", "has_image": True},
            ],
        }
    ],
    "has_next_page": True,
    "next_cursor": "eyJjaGFpbiI6ImV0aGVyZXVtIn0",
    "query": {"network": "ethereum", "limit": 1, "dex_name": "curve", "order_by": "volume_usd_24h"},
}


class TestDexPoolsMigration(unittest.TestCase):
    """pools.list_by_dex must target /pools/search with a dex_name filter.

    DexPaprika removed GET /networks/{network}/dexes/{dex}/pools on 2026-08-05;
    it returns 410. These tests pin the replacement path, the param rename and
    the response shape so the old call cannot come back by accident.
    """

    def setUp(self):
        self.client = DexPaprikaClient()

    def _patched_get(self):
        return patch.object(
            self.client.pools, "_get", return_value=json.loads(json.dumps(LIVE_DEX_SEARCH_BODY))
        )

    def test_targets_pools_search_with_dex_name(self):
        """The DEX moves out of the path and into the dex_name query param."""
        with self._patched_get() as mock_get:
            self.client.pools.list_by_dex("ethereum", "curve", limit=1)

        endpoint = mock_get.call_args.args[0]
        params = mock_get.call_args.kwargs["params"]

        self.assertEqual(endpoint, "/networks/ethereum/pools/search")
        self.assertNotIn("/dexes/", endpoint)
        self.assertEqual(params["dex_name"], "curve")
        self.assertNotIn("dex_id", params)
        # Cursor pagination: no page number goes on the wire.
        self.assertNotIn("page", params)

    def test_legacy_order_by_is_mapped(self):
        """order_by="volume_usd" keeps working and becomes volume_usd_24h."""
        with self._patched_get() as mock_get:
            self.client.pools.list_by_dex("ethereum", "curve", order_by="volume_usd")
        self.assertEqual(mock_get.call_args.kwargs["params"]["order_by"], "volume_usd_24h")

    def test_cursor_is_forwarded(self):
        """Paging uses cursor, not page."""
        with self._patched_get() as mock_get:
            self.client.pools.list_by_dex("ethereum", "curve", cursor="abc123", page=7)
        params = mock_get.call_args.kwargs["params"]
        self.assertEqual(params["cursor"], "abc123")
        self.assertNotIn("page", params)

    def test_response_shape_matches_live_sample(self):
        """Rows under results, cursor envelope, volume_usd_24h on each row."""
        with self._patched_get():
            response = self.client.pools.list_by_dex("ethereum", "curve", limit=1)

        self.assertTrue(response.has_next_page)
        self.assertEqual(response.next_cursor, "eyJjaGFpbiI6ImV0aGVyZXVtIn0")
        self.assertEqual(len(response.results), 1)
        # `.pools` is the backward-compatible alias for `.results`.
        self.assertEqual(response.pools, response.results)
        # There is no page_info on the search endpoint.
        self.assertFalse(hasattr(response, "page_info"))

        pool = response.results[0]
        self.assertEqual(pool.id, "0x4f493b7de8aac7d55f71853688b1f7c8f0243c85")
        self.assertEqual(pool.dex_id, "curve")
        self.assertEqual(pool.volume_usd_24h, 15883391.558251368)
        self.assertEqual(pool.transactions_24h, 289)
        self.assertEqual(pool.price_change_percentage_6h, 0.009802157529374174)
        # The removed field names must not reappear on the model.
        self.assertFalse(hasattr(pool, "volume_usd"))
        self.assertFalse(hasattr(pool, "transactions"))
        # Search rows reference tokens by id and chain only.
        self.assertEqual(pool.tokens[0].chain, "ethereum")
        self.assertIsNone(pool.tokens[0].symbol)

    def test_removed_endpoint_raises_typed_error(self):
        """A caller pinned to the old path gets the replacement in the error."""
        response = requests.Response()
        response.status_code = 410
        response._content = json.dumps({
            "code": 410,
            "message": "endpoint removed",
            "replacement": "/networks/:network/pools/search",
        }).encode("utf-8")

        with patch('requests.Session.request', return_value=response):
            with self.assertRaises(DeprecatedEndpointError) as ctx:
                self.client.get("/networks/ethereum/dexes/uniswap_v3/pools")

        self.assertEqual(ctx.exception.replacement, "/networks/:network/pools/search")


if __name__ == "__main__":
    unittest.main() 
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


class TestPriceChangeWindowParams(unittest.TestCase):
    """Test suite for the pool price-change sort fields and filter bounds.

    These assert on the params handed to the transport rather than on a live
    response. The API ignores an unknown filter param and still answers 200 with
    a full unfiltered result set, so a bound that never reaches the wire cannot
    be caught by inspecting the rows. pools.filter() enumerates every bound
    explicitly, which means a single typo silently drops one.
    """

    WINDOWS = ["24h", "6h", "1h", "5m"]

    def setUp(self):
        """Set up test environment."""
        self.client = DexPaprikaClient()

    def _capture_params(self, call):
        """Run ``call`` against a stubbed transport and return the sent params.

        The cache is cleared first: repeated calls that fall back to the same
        canonical params would otherwise be served from cache and never reach
        the transport, leaving nothing to assert on.
        """
        self.client.clear_cache()
        with patch('requests.Session.request') as mock_request:
            mock_response = MagicMock()
            mock_response.status_code = 200
            mock_response.content = b'{"results": []}'
            mock_response.json.return_value = {"results": []}
            mock_request.return_value = mock_response

            call()
            return mock_request.call_args.kwargs["params"]

    def test_every_filter_bound_reaches_the_wire(self):
        """All eight min/max bounds must be sent under their canonical names."""
        for window in self.WINDOWS:
            for bound in ("min", "max"):
                name = f"price_change_percentage_{window}_{bound}"
                # A distinct value per bound: a copy-paste slip that wires two
                # arguments to the same key shows up as a wrong value, not just
                # a missing one.
                value = -12.5 if bound == "max" else 7.5
                params = self._capture_params(
                    lambda: self.client.pools.filter("ethereum", **{name: value})
                )
                self.assertIn(name, params, f"{name} never reached the request")
                self.assertEqual(params[name], value, name)

    def test_negative_bounds_are_preserved(self):
        """A negative bound is the normal case: max=-20 means down at least 20%."""
        params = self._capture_params(
            lambda: self.client.pools.filter(
                "ethereum", price_change_percentage_24h_max=-20
            )
        )
        self.assertEqual(params["price_change_percentage_24h_max"], -20)

    def test_zero_bound_is_not_dropped(self):
        """0 is a meaningful bound (any pool that is up) and must survive
        the None-stripping in _clean_params."""
        params = self._capture_params(
            lambda: self.client.pools.filter(
                "ethereum", price_change_percentage_1h_min=0
            )
        )
        self.assertEqual(params["price_change_percentage_1h_min"], 0)

    def test_pool_sort_windows_pass_through(self):
        """The short windows must survive canonical mapping on the pool side.

        An unmapped sort field falls back to volume_usd_24h before the request
        is built, so the failure mode is a 200 sorted by the wrong column.
        """
        for window in ("6h", "1h", "5m"):
            field = f"price_change_percentage_{window}"
            params = self._capture_params(
                lambda: self.client.pools.list_by_network("ethereum", order_by=field)
            )
            self.assertEqual(params["order_by"], field)

    def test_short_windows_never_reach_the_token_endpoint(self):
        """Pool-only windows must fall back rather than be forwarded to tokens.

        /networks/{network}/tokens/search returns 400 for the short windows and
        token rows carry no 5m field. Forwarding one would turn a working call
        into an error.
        """
        for window in ("6h", "1h", "5m"):
            field = f"price_change_percentage_{window}"
            params = self._capture_params(
                lambda: self.client.tokens.get_top("ethereum", order_by=field)
            )
            self.assertEqual(params["order_by"], "volume_usd_24h")

    def test_token_filter_has_no_price_change_bounds(self):
        """Pin the asymmetry so a later sweep does not add these to tokens."""
        import inspect

        token_args = inspect.signature(self.client.tokens.filter).parameters
        pool_args = inspect.signature(self.client.pools.filter).parameters

        for window in self.WINDOWS:
            for bound in ("min", "max"):
                name = f"price_change_percentage_{window}_{bound}"
                self.assertIn(name, pool_args, f"pools.filter lost {name}")
                self.assertNotIn(name, token_args, f"tokens.filter gained {name}")


if __name__ == "__main__":
    unittest.main() 
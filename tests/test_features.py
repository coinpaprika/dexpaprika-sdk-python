#!/usr/bin/env python3
"""
Test script to verify caching and retry behavior in the DexPaprika SDK.
"""

import unittest
import time
from datetime import timedelta
from unittest.mock import patch, MagicMock
import requests
from requests.exceptions import ConnectionError, Timeout, HTTPError

from dexpaprika_sdk import DexPaprikaClient


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


if __name__ == "__main__":
    unittest.main() 
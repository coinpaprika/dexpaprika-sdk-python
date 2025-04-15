#!/usr/bin/env python3
"""
Test script to verify parameter validation in the DexPaprika SDK.
"""

import unittest
from dexpaprika_sdk import DexPaprikaClient

class TestParameterValidation(unittest.TestCase):
    """Test suite for parameter validation."""
    
    def setUp(self):
        """Set up test environment."""
        self.client = DexPaprikaClient()
    
    def test_required_parameters(self):
        """Test validation of required parameters."""
        # Test empty network_id
        with self.assertRaises(ValueError) as context:
            self.client.pools.list_by_network(network_id="")
        self.assertIn("network_id is required", str(context.exception))
        
        # Test None network_id
        with self.assertRaises(ValueError) as context:
            self.client.pools.list_by_network(network_id=None)
        self.assertIn("network_id is required", str(context.exception))
        
        # Test empty pool_address
        with self.assertRaises(ValueError) as context:
            self.client.pools.get_details(network_id="ethereum", pool_address="")
        self.assertIn("pool_address is required", str(context.exception))
    
    def test_enum_validation(self):
        """Test validation of enum parameters."""
        # Test invalid sort order
        with self.assertRaises(ValueError) as context:
            self.client.pools.list(sort="invalid")
        self.assertIn("sort must be one of: asc, desc", str(context.exception))
        
        # Test invalid order_by
        with self.assertRaises(ValueError) as context:
            self.client.pools.list(order_by="invalid")
        self.assertIn("order_by must be one of:", str(context.exception))
        
        # Test invalid interval
        with self.assertRaises(ValueError) as context:
            self.client.pools.get_ohlcv(
                network_id="ethereum", 
                pool_address="0x88e6a0c2ddd26feeb64f039a2c41296fcb3f5640", 
                start="2023-01-01", 
                interval="invalid"
            )
        self.assertIn("interval must be one of:", str(context.exception))
    
    def test_range_validation(self):
        """Test validation of numeric range parameters."""
        # Test negative page
        with self.assertRaises(ValueError) as context:
            self.client.pools.list(page=-1)
        self.assertIn("page must be at least 0", str(context.exception))
        
        # Test invalid limit (too low)
        with self.assertRaises(ValueError) as context:
            self.client.pools.list(limit=0)
        self.assertIn("limit must be at least 1", str(context.exception))
        
        # Test invalid limit (too high)
        with self.assertRaises(ValueError) as context:
            self.client.pools.list(limit=101)
        self.assertIn("limit must be at most 100", str(context.exception))

if __name__ == "__main__":
    unittest.main() 
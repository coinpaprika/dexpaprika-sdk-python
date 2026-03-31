#!/usr/bin/env python3

import sys
import os
import time
import pytest
from datetime import datetime, timedelta

# Add the parent directory to the path so we can import the package
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '.')))

from dexpaprika_sdk import DexPaprikaClient

# Create a fixture for the client to be reused across tests
@pytest.fixture
def client():
    return DexPaprikaClient()

# Create a fixture for test data
@pytest.fixture
def test_data():
    return {
        "ethereum_network": "ethereum",
        "test_pool_network": "ethereum",
        "test_pool_address": "0x88e6a0c2ddd26feeb64f039a2c41296fcb3f5640",  # USDC/WETH on Uniswap v3
        "test_dex": "uniswap_v3",  # Uniswap V3 on Ethereum
        "test_token_address": "0xa0b86991c6218b36c1d19d4a2e9eb0ce3606eb48",  # USDC on Ethereum
        "start_date": (datetime.now() - timedelta(days=7)).strftime("%Y-%m-%d"),
        "end_date": datetime.now().strftime("%Y-%m-%d"),
    }

# Networks API tests
def test_networks_list(client):
    networks = client.networks.list()
    assert networks is not None
    assert len(networks) > 0

def test_networks_list_dexes(client, test_data):
    dexes = client.networks.list_dexes(test_data["ethereum_network"])
    assert dexes is not None
    assert hasattr(dexes, 'dexes')

# Utils API tests
def test_utils_get_stats(client):
    stats = client.utils.get_stats()
    assert stats is not None
    assert hasattr(stats, 'chains')
    assert hasattr(stats, 'pools')
    assert hasattr(stats, 'tokens')

# Pools API tests
def test_pools_list_deprecated(client):
    """Test the deprecated global pools method with deprecation warning."""
    import warnings
    with warnings.catch_warnings(record=True) as w:
        warnings.simplefilter("always")
        pools_response = client.pools.list(limit=5)
        assert pools_response is not None
        assert hasattr(pools_response, 'pools')
        assert len(pools_response.pools) > 0
        # Check that a deprecation warning was issued
        assert len(w) > 0
        assert any("deprecated" in str(warning.message).lower() for warning in w)

def test_pools_list_by_network_primary(client, test_data):
    """Test the primary pools list method using network-specific endpoint."""
    pools_response = client.pools.list_by_network(test_data["ethereum_network"], limit=5)
    assert pools_response is not None
    assert hasattr(pools_response, 'pools')
    assert len(pools_response.pools) > 0

def test_dexes_list(client, test_data):
    dexes_response = client.dexes.list(test_data["ethereum_network"])
    assert dexes_response is not None
    assert hasattr(dexes_response, 'dexes')

def test_pools_list_by_dex(client, test_data):
    pools_response = client.pools.list_by_dex(
        test_data["ethereum_network"], 
        test_data["test_dex"], 
        limit=5
    )
    assert pools_response is not None
    assert hasattr(pools_response, 'pools')

def test_pools_get_details(client, test_data):
    pool_details = client.pools.get_details(
        test_data["test_pool_network"], 
        test_data["test_pool_address"]
    )
    assert pool_details is not None
    assert hasattr(pool_details, 'tokens')

def test_pools_get_ohlcv(client, test_data):
    ohlcv = client.pools.get_ohlcv(
        test_data["test_pool_network"],
        test_data["test_pool_address"],
        start=test_data["start_date"],
        end=test_data["end_date"],
        limit=5,
        interval="24h"
    )
    assert ohlcv is not None

def test_pools_get_transactions(client, test_data):
    transactions = client.pools.get_transactions(
        test_data["test_pool_network"], 
        test_data["test_pool_address"], 
        limit=5
    )
    assert transactions is not None
    assert hasattr(transactions, 'transactions')

# Tokens API tests
def test_tokens_get_details(client, test_data):
    token_details = client.tokens.get_details(
        test_data["test_pool_network"], 
        test_data["test_token_address"]
    )
    assert token_details is not None
    assert hasattr(token_details, 'name')
    assert hasattr(token_details, 'symbol')

def test_tokens_get_pools(client, test_data):
    token_pools = client.tokens.get_pools(
        test_data["test_pool_network"], 
        test_data["test_token_address"], 
        limit=5
    )
    assert token_pools is not None
    assert hasattr(token_pools, 'pools')

def test_tokens_get_pools_with_reorder(client, test_data):
    """Test the tokens.get_pools method with the new reorder parameter."""
    token_pools = client.tokens.get_pools(
        test_data["test_pool_network"], 
        test_data["test_token_address"], 
        limit=5,
        reorder=True
    )
    assert token_pools is not None
    assert hasattr(token_pools, 'pools')

# Pool Filter API tests
def test_pools_filter(client, test_data):
    """Test pool filtering with volume constraint."""
    filtered = client.pools.filter(
        test_data["ethereum_network"],
        volume_24h_min=100000,
        limit=5
    )
    assert filtered is not None
    assert hasattr(filtered, 'results')
    assert hasattr(filtered, 'page_info')
    assert len(filtered.results) > 0
    # Verify each pool has the expected fields
    pool = filtered.results[0]
    assert hasattr(pool, 'id')
    assert hasattr(pool, 'volume_usd')
    assert hasattr(pool, 'tokens')

def test_pools_filter_multiple_params(client, test_data):
    """Test pool filtering with multiple constraints."""
    filtered = client.pools.filter(
        test_data["ethereum_network"],
        volume_24h_min=50000,
        txns_24h_min=10,
        sort_by="volume_24h",
        sort_dir="desc",
        limit=3
    )
    assert filtered is not None
    assert hasattr(filtered, 'results')

# Top Tokens API tests
def test_tokens_get_top(client, test_data):
    """Test getting top tokens on a network."""
    top_tokens = client.tokens.get_top(test_data["ethereum_network"], limit=5)
    assert top_tokens is not None
    assert hasattr(top_tokens, 'tokens')
    assert hasattr(top_tokens, 'page_info')
    assert len(top_tokens.tokens) > 0
    # Verify token structure
    token = top_tokens.tokens[0]
    assert hasattr(token, 'address')
    assert hasattr(token, 'name')
    assert hasattr(token, 'symbol')
    assert hasattr(token, 'price_usd')

def test_tokens_get_top_with_sort(client, test_data):
    """Test getting top tokens with custom sorting."""
    top_tokens = client.tokens.get_top(
        test_data["ethereum_network"],
        order_by="volume_24h",
        sort="asc",
        limit=3
    )
    assert top_tokens is not None
    assert hasattr(top_tokens, 'tokens')

# Token Filter API tests
def test_tokens_filter(client, test_data):
    """Test token filtering with volume constraint."""
    filtered = client.tokens.filter(
        test_data["ethereum_network"],
        volume_24h_min=100000,
        limit=5
    )
    assert filtered is not None
    assert hasattr(filtered, 'results')
    assert hasattr(filtered, 'page_info')
    assert len(filtered.results) > 0
    # Verify token structure
    token = filtered.results[0]
    assert hasattr(token, 'address')
    assert hasattr(token, 'chain')
    assert hasattr(token, 'price_usd')

def test_tokens_filter_multiple_params(client, test_data):
    """Test token filtering with multiple constraints."""
    filtered = client.tokens.filter(
        test_data["ethereum_network"],
        volume_24h_min=100000,
        fdv_min=1000000,
        sort_by="volume_24h",
        sort_dir="desc",
        limit=3
    )
    assert filtered is not None
    assert hasattr(filtered, 'results')

# Multi Prices API tests
def test_tokens_get_multi_prices(client, test_data):
    """Test getting batch prices for multiple tokens."""
    prices = client.tokens.get_multi_prices(
        test_data["ethereum_network"],
        tokens=[
            "0xc02aaa39b223fe8d0a0e5c4f27ead9083c756cc2",  # WETH
            test_data["test_token_address"],  # USDC
        ]
    )
    assert prices is not None
    assert isinstance(prices, list)
    assert len(prices) == 2
    # Verify price structure
    price = prices[0]
    assert hasattr(price, 'id')
    assert hasattr(price, 'chain')
    assert hasattr(price, 'price_usd')

def test_tokens_get_multi_prices_single(client, test_data):
    """Test batch prices with a single token."""
    prices = client.tokens.get_multi_prices(
        test_data["ethereum_network"],
        tokens=[test_data["test_token_address"]]
    )
    assert prices is not None
    assert isinstance(prices, list)
    assert len(prices) == 1

def test_tokens_get_multi_prices_validation(client, test_data):
    """Test that empty tokens list raises ValueError."""
    with pytest.raises(ValueError):
        client.tokens.get_multi_prices(test_data["ethereum_network"], tokens=[])

# Search API tests
def test_search_search(client):
    search_results = client.search.search("Jockey")
    assert search_results is not None
    assert hasattr(search_results, 'tokens')
    assert hasattr(search_results, 'pools')
    assert hasattr(search_results, 'dexes')

# Ensure the main function still works when script is run directly
if __name__ == "__main__":
    # Create client
    client = DexPaprikaClient()
    test_data = {
        "ethereum_network": "ethereum",
        "test_pool_network": "ethereum",
        "test_pool_address": "0x88e6a0c2ddd26feeb64f039a2c41296fcb3f5640",
        "test_dex": "uniswap_v3",
        "test_token_address": "0xa0b86991c6218b36c1d19d4a2e9eb0ce3606eb48",
        "start_date": (datetime.now() - timedelta(days=7)).strftime("%Y-%m-%d"),
        "end_date": datetime.now().strftime("%Y-%m-%d"),
    }
    
    # Run all test functions
    print("Running tests manually...")
    test_functions = [
        test_networks_list,
        test_networks_list_dexes,
        test_utils_get_stats,
        test_pools_list_deprecated,
        test_pools_list_by_network_primary,
        test_dexes_list,
        test_pools_list_by_dex,
        test_pools_get_details,
        test_pools_get_ohlcv,
        test_pools_get_transactions,
        test_pools_filter,
        test_pools_filter_multiple_params,
        test_tokens_get_details,
        test_tokens_get_pools,
        test_tokens_get_pools_with_reorder,
        test_tokens_get_top,
        test_tokens_get_top_with_sort,
        test_tokens_filter,
        test_tokens_filter_multiple_params,
        test_tokens_get_multi_prices,
        test_tokens_get_multi_prices_single,
        test_search_search,
    ]
    
    success_count = 0
    failure_count = 0
    
    for test_func in test_functions:
        print(f"Testing {test_func.__name__}...")
        try:
            if test_func.__name__ in ["test_networks_list", "test_utils_get_stats", "test_pools_list_deprecated", "test_search_search"]:
                test_func(client)
            else:
                test_func(client, test_data)
            print(f"✅ {test_func.__name__} - SUCCESS")
            success_count += 1
        except Exception as e:
            print(f"❌ {test_func.__name__} - FAILED: {str(e)}")
            import traceback
            traceback.print_exc()
            failure_count += 1
    
    # Print summary
    print("\n" + "-" * 50 + "\n")
    print(f"SUMMARY: {success_count} endpoints succeeded, {failure_count} endpoints failed")
    print("\n" + "-" * 50 + "\n")
    
    if failure_count > 0:
        sys.exit(1)
    else:
        print("All endpoints tested successfully!") 
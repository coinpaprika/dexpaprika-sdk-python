#!/usr/bin/env python3

import sys
import os
import time
from datetime import datetime, timedelta
import traceback

# Add the parent directory to the path so we can import the package
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '.')))

from dexpaprika_sdk import DexPaprikaClient

def print_separator():
    print("\n" + "-" * 50 + "\n")

def test_endpoint(name, test_func):
    print(f"Testing {name}...")
    try:
        result = test_func()
        print(f"✅ {name} - SUCCESS")
        return True, result
    except Exception as e:
        print(f"❌ {name} - FAILED: {str(e)}")
        traceback.print_exc()
        return False, None

def main():
    # Create a new DexPaprika client
    client = DexPaprikaClient()
    ethereum_network = "ethereum"
    success_count = 0
    failure_count = 0
    
    # 1. Test Networks API
    print_separator()
    print("TESTING NETWORKS API")
    print_separator()
    
    success, networks = test_endpoint("networks.list", lambda: client.networks.list())
    if success:
        success_count += 1
        print(f"Found {len(networks)} networks")
    else:
        failure_count += 1
    
    success, _ = test_endpoint("networks.list_dexes", lambda: client.networks.list_dexes(ethereum_network))
    if success:
        success_count += 1
    else:
        failure_count += 1
    
    # 2. Test Utils API
    print_separator()
    print("TESTING UTILS API")
    print_separator()
    
    success, stats = test_endpoint("utils.get_stats", lambda: client.utils.get_stats())
    if success:
        success_count += 1
        print(f"- Chains: {stats.chains}")
        print(f"- Factories: {stats.factories}")
        print(f"- Pools: {stats.pools}")
        print(f"- Tokens: {stats.tokens}")
    else:
        failure_count += 1
    
    # 3. Test Pools API
    print_separator()
    print("TESTING POOLS API")
    print_separator()
    
    success, pools_response = test_endpoint("pools.list", lambda: client.pools.list(limit=5))
    if success:
        success_count += 1
        print(f"Found {len(pools_response.pools)} pools")
        if pools_response.pools:
            # Save the first pool for later tests
            test_pool = pools_response.pools[0]
            test_pool_network = test_pool.chain
            test_pool_address = test_pool.id
            print(f"Using pool {test_pool_address} on {test_pool.chain} for further tests")
    else:
        failure_count += 1
        # Use Ethereum USDC/WETH as fallback
        test_pool_network = "ethereum"
        test_pool_address = "0x88e6a0c2ddd26feeb64f039a2c41296fcb3f5640"  # USDC/WETH on Uniswap v3
    
    success, _ = test_endpoint("pools.list_by_network", lambda: client.pools.list_by_network(ethereum_network, limit=5))
    if success:
        success_count += 1
    else:
        failure_count += 1
    
    success, dexes_response = test_endpoint("dexes.list", lambda: client.dexes.list(ethereum_network))
    if success:
        success_count += 1
        # Use a known popular DEX instead of the first one from the list
        test_dex = "uniswap_v3"  # Uniswap V3 on Ethereum
        
        success, _ = test_endpoint("pools.list_by_dex", lambda: client.pools.list_by_dex(ethereum_network, test_dex, limit=5))
        if success:
            success_count += 1
        else:
            failure_count += 1
    else:
        failure_count += 1
    
    success, pool_details = test_endpoint("pools.get_details", lambda: client.pools.get_details(test_pool_network, test_pool_address))
    if success:
        success_count += 1
        print(f"Pool details: {pool_details.dex_name}")
        if hasattr(pool_details, 'tokens') and len(pool_details.tokens) >= 2:
            # Save token addresses for token API tests
            test_token_address = pool_details.tokens[0].id
            print(f"Using token {test_token_address} for further tests")
    else:
        failure_count += 1
        # Use USDC on Ethereum as fallback
        test_token_address = "0xa0b86991c6218b36c1d19d4a2e9eb0ce3606eb48"  # USDC on Ethereum
    
    # Use dates for OHLCV
    end_date = datetime.now()
    start_date = end_date - timedelta(days=7)
    start_str = start_date.strftime("%Y-%m-%d")
    end_str = end_date.strftime("%Y-%m-%d")
    
    success, _ = test_endpoint("pools.get_ohlcv", lambda: client.pools.get_ohlcv(
        test_pool_network, 
        test_pool_address, 
        start=start_str,
        end=end_str,
        limit=5,
        interval="24h"
    ))
    if success:
        success_count += 1
    else:
        failure_count += 1
    
    success, _ = test_endpoint("pools.get_transactions", lambda: client.pools.get_transactions(test_pool_network, test_pool_address, limit=5))
    if success:
        success_count += 1
    else:
        failure_count += 1
    
    # 4. Test Tokens API
    print_separator()
    print("TESTING TOKENS API")
    print_separator()
    
    success, token_details = test_endpoint("tokens.get_details", lambda: client.tokens.get_details(test_pool_network, test_token_address))
    if success:
        success_count += 1
        print(f"Token details: {token_details.name} ({token_details.symbol})")
    else:
        failure_count += 1
    
    success, _ = test_endpoint("tokens.get_pools", lambda: client.tokens.get_pools(test_pool_network, test_token_address, limit=5))
    if success:
        success_count += 1
    else:
        failure_count += 1
    
    # 5. Test Search API
    print_separator()
    print("TESTING SEARCH API")
    print_separator()
    
    success, search_results = test_endpoint("search.search", lambda: client.search.search("Jockey"))
    if success:
        success_count += 1
        print(f"Found {len(search_results.tokens)} tokens, {len(search_results.pools)} pools, and {len(search_results.dexes)} DEXes")
    else:
        failure_count += 1
    
    # Print summary
    print_separator()
    print(f"SUMMARY: {success_count} endpoints succeeded, {failure_count} endpoints failed")
    print_separator()
    
    if failure_count > 0:
        sys.exit(1)
    else:
        print("All endpoints tested successfully!")

if __name__ == "__main__":
    main() 
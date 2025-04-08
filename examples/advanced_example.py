#!/usr/bin/env python3

"""
Advanced example demonstrating all available API methods in the DexPaprika SDK.
"""

import sys
import os
import time
from datetime import datetime, timedelta

# Add the parent directory to the path so we can import the package
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from dexpaprika_sdk import DexPaprikaClient


def format_currency(amount):
    """Format a currency amount with commas and 2 decimal places."""
    return f"${amount:,.2f}"


def main():
    # Create a new DexPaprika client
    client = DexPaprikaClient()
    
    print("========== DexPaprika SDK Advanced Example ==========\n")
    
    # Get stats
    print("Getting overall statistics...")
    try:
        stats = client.utils.get_stats()
        print(f"DexPaprika Stats:")
        print(f"- Total Chains: {stats.chains}")
        print(f"- Total DEX Factories: {stats.factories}")
        print(f"- Total Pools: {stats.pools:,}")
        print(f"- Total Tokens: {stats.tokens:,}\n")
    except Exception as e:
        print(f"Could not get stats: {e}\n")
    
    # Get networks
    print("Getting list of supported networks...")
    try:
        networks = client.networks.list()
        print(f"Found {len(networks)} networks:")
        for i, network in enumerate(networks[:5]):
            print(f"- {network.display_name} ({network.id})")
        if len(networks) > 5:
            print(f"- ... and {len(networks) - 5} more.\n")
    except Exception as e:
        print(f"Could not get networks: {e}\n")
        # Default to ethereum if we can't get networks
        networks = []
    
    # Choose a network for further queries
    network_id = "ethereum"  # Using Ethereum for this example
    print(f"Using {network_id} network for further queries.\n")
    
    # Get DEXes on this network
    print(f"Getting DEXes on {network_id}...")
    try:
        dexes = client.dexes.list(network=network_id, limit=5)
        print(f"Found {len(dexes.dexes)} DEXes:")
        for i, dex in enumerate(dexes.dexes):
            print(f"- {dex.dex_name} ({dex.protocol})")
        print()
    except Exception as e:
        print(f"Could not get DEXes: {e}\n")
        dexes = None
    
    # Get pools on this network
    print(f"Getting top pools on {network_id}...")
    try:
        pools = client.pools.list_by_network(network_id=network_id, limit=5, order_by="volume_usd", sort="desc")
        print(f"Top 5 pools by volume:")
        for pool in pools.pools:
            token_pair = f"{pool.tokens[0].symbol}/{pool.tokens[1].symbol}" if len(pool.tokens) >= 2 else "Unknown Pair"
            print(f"- {token_pair} on {pool.dex_name}: {format_currency(pool.volume_usd)} volume ({format_currency(pool.price_usd)} price)")
        print()
    except Exception as e:
        print(f"Could not get pools: {e}\n")
        pools = None
    
    # Get pools for a specific DEX
    if dexes and dexes.dexes:
        dex_id = dexes.dexes[0].id
        dex_name = dexes.dexes[0].dex_name
        print(f"Getting top pools for {dex_name}...")
        try:
            dex_pools = client.pools.list_by_dex(
                network_id=network_id, 
                dex_id=dex_id, 
                limit=3, 
                order_by="volume_usd", 
                sort="desc"
            )
            print(f"Top 3 {dex_name} pools by volume:")
            for pool in dex_pools.pools:
                token_pair = f"{pool.tokens[0].symbol}/{pool.tokens[1].symbol}" if len(pool.tokens) >= 2 else "Unknown Pair"
                print(f"- {token_pair}: {format_currency(pool.volume_usd)} volume")
        except Exception as e:
            print(f"Could not get pools for {dex_name}: {e}")
        print()
    
    # Choose a pool for detailed analysis
    if pools and pools.pools:
        pool_address = pools.pools[0].id
        pool_pair = f"{pools.pools[0].tokens[0].symbol}/{pools.pools[0].tokens[1].symbol}" if len(pools.pools[0].tokens) >= 2 else "Unknown Pair"
        print(f"Getting detailed info for {pool_pair} pool...")
        
        # Get pool details
        pool_details = client.pools.get_details(
            network_id=network_id, 
            pool_address=pool_address
        )
        print(f"Pool Details:")
        print(f"- ID: {pool_details.id}")
        print(f"- DEX: {pool_details.dex_name}")
        print(f"- Created: {pool_details.created_at}")
        print(f"- Last Price: {format_currency(pool_details.last_price_usd)}")
        print(f"- 24h Volume: {format_currency(pool_details.day.volume_usd)}")
        print(f"- 24h Transactions: {pool_details.day.txns}")
        print(f"- 24h Price Change: {pool_details.day.last_price_usd_change:.2f}%")
        print()
        
        # Get OHLCV data
        yesterday = datetime.now() - timedelta(days=1)
        yesterday_str = yesterday.strftime("%Y-%m-%d")
        print(f"Getting OHLCV data since {yesterday_str}...")
        
        try:
            ohlcv = client.pools.get_ohlcv(
                network_id=network_id,
                pool_address=pool_address,
                start=yesterday_str,
                interval="6h",
                limit=4
            )
            print(f"OHLCV Data:")
            for i, data_point in enumerate(ohlcv):
                print(f"- Period {i+1}: Open: {format_currency(data_point.open)}, Close: {format_currency(data_point.close)}, Volume: {data_point.volume}")
            print()
        except Exception as e:
            print(f"Could not get OHLCV data: {e}")
            print()
        
        # Get pool transactions
        print(f"Getting recent transactions...")
        try:
            transactions = client.pools.get_transactions(
                network_id=network_id,
                pool_address=pool_address,
                limit=3
            )
            print(f"Recent Transactions:")
            for i, tx in enumerate(transactions.transactions):
                print(f"- TX {i+1}: {tx.amount_0} {tx.token_0} for {tx.amount_1} {tx.token_1}")
            print()
        except Exception as e:
            print(f"Could not get transaction data: {e}")
            print()
        
        # Get token details
        token_address = pool_details.tokens[0].id
        token_symbol = pool_details.tokens[0].symbol
        print(f"Getting details for {token_symbol} token...")
        try:
            token = client.tokens.get_details(network_id=network_id, token_address=token_address)
            print(f"Token Details:")
            print(f"- Name: {token.name} ({token.symbol})")
            print(f"- Total Supply: {token.total_supply:,.0f}")
            print(f"- Decimals: {token.decimals}")
            if token.summary and token.summary.price_usd:
                print(f"- Price: {format_currency(token.summary.price_usd)}")
                if token.summary.fdv:
                    print(f"- Fully Diluted Valuation: {format_currency(token.summary.fdv)}")
            print()
        except Exception as e:
            print(f"Could not get token details: {e}")
            print()
        
        # Get pools for this token
        print(f"Getting pools containing {token_symbol}...")
        try:
            token_pools = client.tokens.get_pools(
                network_id=network_id,
                token_address=token_address,
                limit=3,
                order_by="volume_usd",
                sort="desc"
            )
            print(f"Top 3 {token_symbol} pools by volume:")
            for pool in token_pools.pools:
                other_token = pool.tokens[1].symbol if pool.tokens[0].symbol == token_symbol else pool.tokens[0].symbol
                print(f"- {token_symbol}/{other_token} on {pool.dex_name}: {format_currency(pool.volume_usd)} volume")
            print()
        except Exception as e:
            print(f"Could not get token pools: {e}")
            print()
    
    # Search for something
    search_term = "uniswap"
    print(f"Searching for '{search_term}'...")
    search_results = client.search.search(search_term)
    print(f"Search Results:")
    print(f"- Found {len(search_results.tokens)} tokens")
    print(f"- Found {len(search_results.pools)} pools")
    print(f"- Found {len(search_results.dexes)} DEXes")
    
    if search_results.tokens:
        print("\nTop token result:")
        print(f"- {search_results.tokens[0].name} ({search_results.tokens[0].symbol}) on {search_results.tokens[0].chain}")
    
    if search_results.pools:
        print("\nTop pool result:")
        token_pair = f"{search_results.pools[0].tokens[0].symbol}/{search_results.pools[0].tokens[1].symbol}" if len(search_results.pools[0].tokens) >= 2 else "Unknown Pair"
        print(f"- {token_pair} on {search_results.pools[0].dex_name} ({search_results.pools[0].chain})")
    
    if search_results.dexes:
        print("\nTop DEX result:")
        print(f"- {search_results.dexes[0].dex_name} on {search_results.dexes[0].chain}")
    
    print("\n========== End of Advanced Example ==========")


# Performance tracking example
def perf_test(client):
    print("\n" + "=" * 50)
    print("PERFORMANCE TRACKING EXAMPLE")
    print("=" * 50 + "\n")
    
    # import perf utilities
    from dexpaprika_sdk.utils.perf import get_perf_stats, reset_perf_stats
    
    # reset stats before testing
    reset_perf_stats()
    
    # make a series of API calls
    print("Running performance tests...")
    client.networks.list()
    client.pools.list(limit=5)
    client.pools.list(limit=10)
    client.tokens.get_details("ethereum", "0xc02aaa39b223fe8d0a0e5c4f27ead9083c756cc2") # WETH
    client.tokens.get_pools("ethereum", "0xc02aaa39b223fe8d0a0e5c4f27ead9083c756cc2", limit=5)
    client.search.search("bitcoin")
    
    # get and display stats
    stats = get_perf_stats()
    print("\nPerformance Stats:")
    print("-" * 40)
    for endpoint, data in stats.items():
        print(f"{endpoint}:")
        print(f"  Calls: {data['calls']}")
        print(f"  Avg Time: {data['avg_time']:.6f}s")
        print(f"  Min Time: {data['min_time']:.6f}s")
        print(f"  Max Time: {data['max_time']:.6f}s")
        print("-" * 40)


# call the perf test if run directly
if __name__ == "__main__":
    if "--perf" in sys.argv:
        client = DexPaprikaClient()
        perf_test(client)
    else:
        main() 
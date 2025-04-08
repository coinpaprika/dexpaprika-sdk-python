#!/usr/bin/env python3

import sys
import os

# Add the parent directory to the path so we can import the package
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from dexpaprika_sdk import DexPaprikaClient


def main():
    # Create a new DexPaprika client
    client = DexPaprikaClient()

    # Get a list of networks
    networks = client.networks.list()
    print("Available networks:")
    for network in networks:
        print(f"- {network.display_name} ({network.id})")

    print("\n--------\n")

    # Get stats
    stats = client.utils.get_stats()
    print(f"DexPaprika stats:")
    print(f"- Chains: {stats.chains}")
    print(f"- Factories: {stats.factories}")
    print(f"- Pools: {stats.pools}")
    print(f"- Tokens: {stats.tokens}")

    print("\n--------\n")

    # Get top pools
    pools_resp = client.pools.list(limit=5, order_by="volume_usd", sort="desc")
    print("Top 5 pools by volume:")
    for pool in pools_resp.pools:
        token_pair = f"{pool.tokens[0].symbol}/{pool.tokens[1].symbol}" if len(pool.tokens) >= 2 else "Unknown Pair"
        print(f"- {token_pair} on {pool.dex_name} ({pool.chain}): ${pool.volume_usd:.2f} volume")

    print("\n--------\n")

    # Search for a token
    search_results = client.search.search("bitcoin")
    print("Search results for 'bitcoin':")
    print(f"- Found {len(search_results.tokens)} tokens")
    print(f"- Found {len(search_results.pools)} pools")
    print(f"- Found {len(search_results.dexes)} dexes")

    if search_results.tokens:
        print("\nTop token result:")
        print(f"- {search_results.tokens[0].name} ({search_results.tokens[0].symbol}) on {search_results.tokens[0].chain}")


if __name__ == "__main__":
    main() 
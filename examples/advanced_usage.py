#!/usr/bin/env python3
"""
Example script demonstrating advanced features of the DexPaprika SDK.
"""

import sys
import os
import time
from datetime import timedelta

# Add the parent directory to the path so we can import the package
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from dexpaprika_sdk import DexPaprikaClient


def demonstrate_caching():
    """Demonstrate the caching functionality."""
    print("\n" + "=" * 50)
    print("CACHING DEMONSTRATION")
    print("=" * 50 + "\n")
    
    # Create a client with default settings
    client = DexPaprikaClient()
    
    # First request (uncached)
    print("Making first request (uncached)...")
    start_time = time.time()
    networks = client.networks.list()
    first_duration = time.time() - start_time
    print(f"Found {len(networks)} networks in {first_duration:.4f} seconds")
    
    # Second request (should be cached)
    print("\nMaking second request (should be cached)...")
    start_time = time.time()
    networks_cached = client.networks.list()
    second_duration = time.time() - start_time
    print(f"Found {len(networks_cached)} networks in {second_duration:.4f} seconds")
    print(f"Cache speedup: {(first_duration / second_duration):.1f}x faster")
    
    # Request with skip_cache
    print("\nMaking request with skip_cache=True...")
    start_time = time.time()
    networks_uncached = client.networks.list()
    third_duration = time.time() - start_time
    print(f"Found {len(networks_uncached)} networks in {third_duration:.4f} seconds")
    
    # Request with custom TTL
    print("\nMaking request with custom TTL (10 seconds)...")
    # This is using private API for demonstration purposes
    start_time = time.time()
    networks_custom_ttl = client.networks._get("/networks", ttl=timedelta(seconds=10))
    print(f"Found {len(networks_custom_ttl)} networks")
    
    # Clear cache
    print("\nClearing cache...")
    client.clear_cache()
    
    # Request after cache clear
    print("\nMaking request after cache clear...")
    start_time = time.time()
    networks_after_clear = client.networks.list()
    clear_duration = time.time() - start_time
    print(f"Found {len(networks_after_clear)} networks in {clear_duration:.4f} seconds")


def demonstrate_retry_backoff():
    """Demonstrate the retry with backoff functionality."""
    print("\n" + "=" * 50)
    print("RETRY WITH BACKOFF DEMONSTRATION")
    print("=" * 50 + "\n")
    
    # Custom backoff times
    backoff_times = [0.1, 0.5, 1.0, 5.0]  # 100ms, 500ms, 1s, 5s
    
    # Create a client with custom backoff settings
    client = DexPaprikaClient(
        max_retries=4,
        backoff_times=backoff_times
    )
    
    print(f"Client configured with {client.max_retries} retries")
    print(f"Backoff times: {client.backoff_times} seconds")
    
    # Make a request to demonstrate the retry functionality
    # Note: This will only demonstrate retries if the API is having issues
    print("\nMaking request that might trigger retries...")
    try:
        pools = client.pools.list(limit=5)
        print(f"Request successful, found {len(pools.pools)} pools")
    except Exception as e:
        print(f"Request failed after retries: {e}")
    
    print("\nNote: To properly demonstrate retries, you would need to")
    print("simulate network issues or use a mock server that returns errors.")


def main():
    """Main function to run the demonstrations."""
    print("DexPaprika SDK Advanced Features Example")
    
    demonstrate_caching()
    demonstrate_retry_backoff()
    
    print("\nDemo completed!")


if __name__ == "__main__":
    main() 
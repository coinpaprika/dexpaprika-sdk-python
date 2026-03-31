# DexPaprika Python SDK

[![PyPI version](https://badge.fury.io/py/dexpaprika-sdk.svg)](https://badge.fury.io/py/dexpaprika-sdk)
[![Python Version](https://img.shields.io/pypi/pyversions/dexpaprika-sdk)](https://pypi.org/project/dexpaprika-sdk/)
[![Tests](https://github.com/coinpaprika/dexpaprika-sdk-python/actions/workflows/tests.yml/badge.svg)](https://github.com/coinpaprika/dexpaprika-sdk-python/actions/workflows/tests.yml)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

A Python client for the DexPaprika API. This SDK provides easy access to real-time data from decentralized exchanges across multiple blockchain networks.

## Features

- Access data from 33+ blockchain networks
- Query information about DEXes, liquidity pools, and tokens
- Get detailed price information, trading volume, and transactions
- **Filter pools and tokens** by volume, liquidity, FDV, transactions, and creation date
- **Get top tokens** on any network ranked by volume or other metrics
- **Batch price lookups** for up to 10 tokens in a single request
- Search across the entire DexPaprika ecosystem
- Automatic parameter validation with clear error messages
- Type-safe response objects using Pydantic models
- Built-in retry with exponential backoff for API failures
- Intelligent caching system with TTL-based expiration

## Installation

```bash
# Install via pip
pip install dexpaprika-sdk

# Or install from source
git clone https://github.com/coinpaprika/dexpaprika-sdk-python.git
cd dexpaprika-sdk-python
pip install -e .
```

## Migration Guide (v0.3.0)

**Important:** Version 0.3.0 includes breaking changes due to DexPaprika API v1.3.0 updates.

### Global Pools Endpoint Deprecation

The global `/pools` endpoint has been removed. If you were using `client.pools.list()`, you need to update your code:

**Before (deprecated):**
```python
# This method is deprecated and will show warnings
pools = client.pools.list(limit=10)
```

**After (recommended):**
```python
# Use network-specific methods instead
eth_pools = client.pools.list_by_network("ethereum", limit=10)
solana_pools = client.pools.list_by_network("solana", limit=10)
```

### New Token Pools Features

The `tokens.get_pools()` method now supports a new `reorder` parameter:

```python
# Reorder pools so the specified token becomes primary for all metrics
pools = client.tokens.get_pools(
    network_id="ethereum",
    token_address="0xa0b86a33e6441b8466395bf92e8aa0cb53ad20aa",  # USDC
    reorder=True  # Makes USDC the primary token for calculations
)
```

### Backward Compatibility

For backward compatibility, the deprecated `pools.list()` method will:
- Show deprecation warnings
- Automatically fall back to Ethereum network
- Continue working until a future version

We strongly recommend updating your code to use network-specific methods for better performance and future compatibility.

## Usage

### Basic Example

```python
from dexpaprika_sdk import DexPaprikaClient

# Create a new client
client = DexPaprikaClient()

# Get a list of supported networks
networks = client.networks.list()
for network in networks:
    print(f"- {network.display_name} ({network.id})")

# Get stats about the DexPaprika ecosystem
stats = client.utils.get_stats()
print(f"DexPaprika stats: {stats.chains} chains, {stats.pools} pools")

# Get top pools by volume (network-specific)
pools = client.pools.list_by_network(
    network_id="ethereum",
    limit=5, 
    order_by="volume_usd", 
    sort="desc"
)
for pool in pools.pools:
    token_pair = f"{pool.tokens[0].symbol}/{pool.tokens[1].symbol}" if len(pool.tokens) >= 2 else "Unknown Pair"
    print(f"- {token_pair} on {pool.dex_name} ({pool.chain}): ${pool.volume_usd:.2f} volume")
```

### Advanced Examples

#### Get pools for a specific network

```python
# Get top Ethereum pools
eth_pools = client.pools.list_by_network(
    network_id="ethereum", 
    limit=5, 
    order_by="volume_usd", 
    sort="desc"
)
```

#### Get pools for a specific DEX

```python
# Get top Uniswap V3 pools on Ethereum
uniswap_pools = client.pools.list_by_dex(
    network_id="ethereum", 
    dex_id="uniswap_v3", 
    limit=5, 
    order_by="volume_usd", 
    sort="desc"
)
```

#### Get details for a specific pool

```python
# Get details for a specific pool
pool_details = client.pools.get_details(
    network_id="ethereum", 
    pool_address="0x88e6a0c2ddd26feeb64f039a2c41296fcb3f5640"  # USDC/WETH Uniswap v3 pool
)
```

#### Get OHLCV data for a pool

```python
from datetime import datetime, timedelta

# Get OHLCV data for the last 7 days
end_date = datetime.now()
start_date = end_date - timedelta(days=7)
ohlcv_data = client.pools.get_ohlcv(
    network_id="ethereum",
    pool_address="0x88e6a0c2ddd26feeb64f039a2c41296fcb3f5640",
    start=start_date.strftime("%Y-%m-%d"),
    end=end_date.strftime("%Y-%m-%d"),
    interval="24h",
    limit=7
)
```

#### Filter pools by metrics

```python
# Find high-volume Ethereum pools
filtered = client.pools.filter(
    network_id="ethereum",
    volume_24h_min=100000,
    txns_24h_min=50,
    sort_by="volume_24h",
    sort_dir="desc",
    limit=10
)
for pool in filtered.results:
    token_pair = f"{pool.tokens[0].symbol}/{pool.tokens[1].symbol}" if len(pool.tokens) >= 2 else "Unknown"
    print(f"- {token_pair}: ${pool.volume_usd:,.0f} volume")
```

#### Get top tokens on a network

```python
# Get top tokens by volume on Ethereum
top = client.tokens.get_top("ethereum", order_by="volume_24h", limit=5)
for token in top.tokens:
    print(f"- {token.symbol}: ${token.price_usd:.4f} (24h vol: ${token.day.volume_usd:,.0f})")
```

#### Filter tokens by criteria

```python
# Find tokens with high volume and FDV
filtered = client.tokens.filter(
    network_id="ethereum",
    volume_24h_min=100000,
    fdv_min=1000000,
    limit=10
)
for token in filtered.results:
    print(f"- {token.address}: ${token.volume_usd_24h:,.0f} vol, ${token.fdv_usd:,.0f} FDV")
```

#### Get batch prices for multiple tokens

```python
# Get prices for WETH and USDC in one request
prices = client.tokens.get_multi_prices(
    network_id="ethereum",
    tokens=[
        "0xc02aaa39b223fe8d0a0e5c4f27ead9083c756cc2",  # WETH
        "0xa0b86991c6218b36c1d19d4a2e9eb0ce3606eb48",  # USDC
    ]
)
for p in prices:
    print(f"- {p.id}: ${p.price_usd:.4f}")
```

#### Get tokens and pools by search query

```python
# Search for "bitcoin" across the ecosystem
search_results = client.search.search("bitcoin")
print(f"Found {len(search_results.tokens)} tokens and {len(search_results.pools)} pools")
```

### Caching System

The SDK includes an intelligent caching system that helps reduce API calls and improve performance:

```python
# Caching is enabled by default for all GET requests
# First request will be fetched from the API
networks = client.networks.list()

# Subsequent requests will use the cached data (faster)
cached_networks = client.networks.list()

# You can skip the cache when you need fresh data
fresh_networks = client.networks._get("/networks", skip_cache=True)

# Clear the entire cache
client.clear_cache()

# Clear cache only for specific endpoints
client.clear_cache(endpoint_prefix="/networks")
```

Different types of data have different cache durations:
- Network data: 24 hours
- Pool data: 5 minutes
- Token data: 10 minutes
- Statistics: 15 minutes
- Other data: 5 minutes (default)

### Retry with Backoff

The SDK automatically retries failed API requests with exponential backoff:

```python
# Create a client with custom retry settings
client = DexPaprikaClient(
    max_retries=4,  # Number of retry attempts (default: 4)
    backoff_times=[0.1, 0.5, 1.0, 5.0]  # Backoff times in seconds
)

# All API requests will now use these retry settings
# The SDK will retry automatically on connection errors and server errors (5xx)
```

Default retry behavior:
- Retries up to 4 times on connection errors, timeouts, and server errors (5xx)
- Uses backoff intervals of 100ms, 500ms, 1s, and 5s with random jitter
- Does not retry on client errors (4xx) like 404 or 403

### Parameter Validation

The SDK automatically validates parameters before making API requests to help you avoid errors:

```python
# Invalid parameter examples will raise helpful error messages
try:
    # Invalid network ID
    client.pools.list_by_network(network_id="", limit=5)
except ValueError as e:
    print(e)  # "network_id is required"
    
try:
    # Invalid sort parameter
    client.pools.list(sort="invalid_sort")
except ValueError as e:
    print(e)  # "sort must be one of: asc, desc"
    
try:
    # Invalid limit parameter
    client.pools.list(limit=500)
except ValueError as e:
    print(e)  # "limit must be at most 100"
```

### Error Handling

Handle API errors gracefully by using try/except blocks:

```python
try:
    # Try to fetch pool details
    pool_details = client.pools.get_details(
        network_id="ethereum",
        pool_address="0xInvalidAddress"
    )
except Exception as e:
    if "404" in str(e):
        print("Pool not found")
    elif "429" in str(e):
        print("Rate limit exceeded")
    else:
        print(f"An error occurred: {e}")
```

### Working with Models

All API responses are converted to typed Pydantic models for easier access and better code reliability:

```python
# Get pool details
pool = client.pools.get_details(
    network_id="ethereum",
    pool_address="0x88e6a0c2ddd26feeb64f039a2c41296fcb3f5640"
)

# Access pool properties
print(f"Pool: {pool.tokens[0].symbol}/{pool.tokens[1].symbol}")
print(f"Volume (24h): ${pool.day.volume_usd:.2f}")
print(f"Transactions (24h): {pool.day.txns}")
print(f"Price: ${pool.last_price_usd:.4f}")

# Time interval data is available for multiple timeframes
print(f"1h price change: {pool.hour1.last_price_usd_change:.2f}%")
print(f"24h price change: {pool.day.last_price_usd_change:.2f}%")
```

## API Reference

The SDK provides the following main components:

- `NetworksAPI`: Access information about supported blockchain networks
- `PoolsAPI`: Query data about liquidity pools across networks, filter pools by metrics
- `TokensAPI`: Access token information, top tokens, filter tokens, batch price lookups
- `DexesAPI`: Get information about decentralized exchanges
- `SearchAPI`: Search for tokens, pools, and DEXes
- `UtilsAPI`: Utility endpoints like global statistics

## Publishing

For developers contributing to this package, here's how to publish a new version:

1. Update the version in `dexpaprika_sdk/__init__.py`
2. Update the `CHANGELOG.md`
3. Create a new release in GitHub
4. GitHub Actions will automatically build and publish to PyPI

## Development Setup

```bash
# Clone the repository
git clone https://github.com/coinpaprika/dexpaprika-sdk-python.git
cd dexpaprika-sdk-python

# Create a virtual environment (optional)
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate

# Install dev dependencies
pip install -e ".[dev]"
```

## Running Tests

```bash
# Run tests with pytest
pytest

# Run with coverage
pytest --cov=dexpaprika_sdk tests/
```

## Resources

- [Official Documentation](https://docs.dexpaprika.com) - Comprehensive API reference
- [DexPaprika Website](https://dexpaprika.com) - Main product website
- [CoinPaprika](https://coinpaprika.com) - Related cryptocurrency data platform
- [Discord Community](https://discord.gg/DhJge5TUGM) - Get support and connect with other developers
- [PyPI Package](https://pypi.org/project/dexpaprika-sdk/) - Python package details

## License

MIT License 
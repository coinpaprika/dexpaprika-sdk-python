# DexPaprika Python SDK

A Python client for the DexPaprika API. This SDK provides easy access to real-time data from decentralized exchanges across multiple blockchain networks.

## Features

- Access data from 20+ blockchain networks
- Query information about DEXes, liquidity pools, and tokens
- Get detailed price information, trading volume, and transactions
- Search across the entire DexPaprika ecosystem

## Installation

```bash
# Install via pip
pip install dexpaprika-sdk

# Or install from source
git clone https://github.com/donbagger/dexpaprika-sdk-python.git
cd dexpaprika-sdk-python
pip install -e .
```

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

# Get top pools by volume
pools = client.pools.list(limit=5, order_by="volume_usd", sort="desc")
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

#### Get tokens and pools by search query

```python
# Search for "bitcoin" across the ecosystem
search_results = client.search.search("bitcoin")
print(f"Found {len(search_results.tokens)} tokens and {len(search_results.pools)} pools")
```

## API Reference

The SDK provides the following main components:

- `NetworksAPI`: Access information about supported blockchain networks
- `PoolsAPI`: Query data about liquidity pools across networks
- `TokensAPI`: Access token information and related pools
- `DexesAPI`: Get information about decentralized exchanges
- `SearchAPI`: Search for tokens, pools, and DEXes
- `UtilsAPI`: Utility endpoints like global statistics

## License

MIT License 
import pytest
from unittest.mock import MagicMock, patch
import sys
import os
import json
from datetime import datetime
from pathlib import Path

# Add the parent directory to the path so we can import the package
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from dexpaprika_sdk import DexPaprikaClient
from dexpaprika_sdk.models import (
    Network, Dex, DexesResponse, PageInfo,
    Token, Pool, PoolsResponse, TimeIntervalMetrics,
    PoolSearchResponse, PoolSearchResult, PoolSearchToken,
    PoolDetails, OHLCVRecord, Transaction, TransactionsResponse,
    TokenSummary, TokenDetails,
    DexInfo, SearchResult,
    Stats
)

# Create a fixture for determining whether to use mocks or real API
@pytest.fixture
def use_mocks():
    # Set this to False to use the real API instead of mocks
    return True

# Create a fixture for the mock or real client based on the use_mocks flag
@pytest.fixture
def client(use_mocks):
    if use_mocks:
        return create_mock_client()
    else:
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
        "start_date": (datetime.now()).strftime("%Y-%m-%d"),
        "end_date": (datetime.now()).strftime("%Y-%m-%d"),
    }

def create_mock_client():
    """Creates a mocked client that returns pre-defined responses for tests"""
    client = DexPaprikaClient()
    
    # Mock Networks API
    networks = [Network(id="ethereum", display_name="Ethereum")]
    client.networks.list = MagicMock(return_value=networks)
    
    # Field names follow GET /networks/{network}/dexes: the identifier is
    # dex_id, and dex_name is the display name.
    dexes_response = DexesResponse(
        dexes=[Dex(dex_id="uniswap_v3", dex_name="Uniswap V3", chain="ethereum",
                   protocol="uniswapv3", volume_usd_24h=49828928.93,
                   txns_24h=12345, pools_count=678)],
        page_info=PageInfo(limit=10, page=1, total_items=1, total_pages=1),
    )
    client.networks.list_dexes = MagicMock(return_value=dexes_response)
    client.dexes.list = MagicMock(return_value=dexes_response)
    
    # Mock Utils API
    stats = Stats(chains=20, factories=100, pools=5000, tokens=10000)
    client.utils.get_stats = MagicMock(return_value=stats)
    
    # Mock Pools API
    token1 = Token(id="0xa0b86991c6218b36c1d19d4a2e9eb0ce3606eb48", name="USD Coin", symbol="USDC")
    token2 = Token(id="0xc02aaa39b223fe8d0a0e5c4f27ead9083c756cc2", name="Wrapped Ether", symbol="WETH")
    
    pool = Pool(
        id="0x88e6a0c2ddd26feeb64f039a2c41296fcb3f5640",
        chain="ethereum",
        dex_id="uniswap_v3",
        dex_name="Uniswap V3",
        volume_usd=1000000.0,
        tokens=[token1, token2]
    )
    
    pools_response = PoolsResponse(
        pools=[pool],
        page_info=None
    )

    # /pools/search shape, copied from a live response captured 2026-08-05.
    # Rows sit under `results` with has_next_page / next_cursor. There is no
    # bare volume_usd and no page_info, so do not reuse `pools_response` here.
    search_response = PoolSearchResponse(
        results=[
            PoolSearchResult(
                id="0x4f493b7de8aac7d55f71853688b1f7c8f0243c85",
                dex_id="curve",
                dex_name="Curve",
                chain="ethereum",
                volume_usd_24h=15883391.558251368,
                volume_usd_7d=31781851.73428885,
                volume_usd_30d=136889876.39037386,
                liquidity_usd=7407910.088430515,
                transactions_24h=289,
                price_usd=0.9995787501356217,
                created_at="2025-01-25T17:20:47Z",
                created_at_block_number=21702976,
                tokens=[
                    PoolSearchToken(id="0xa0b86991c6218b36c1d19d4a2e9eb0ce3606eb48", chain="ethereum", has_image=True),
                    PoolSearchToken(id="0xdac17f958d2ee523a2206206994597c13d831ec7", chain="ethereum", has_image=True),
                ],
            )
        ],
        has_next_page=True,
        next_cursor="eyJjaGFpbiI6ImV0aGVyZXVtIn0",
    )

    client.pools.list = MagicMock(return_value=search_response)
    client.pools.list_by_network = MagicMock(return_value=search_response)
    client.pools.list_by_dex = MagicMock(return_value=search_response)
    
    # Mock Pool Details
    time_metrics = TimeIntervalMetrics(
        volume_usd=1000000.0,
        txns=500,
        last_price_usd=1800.0,
        last_price_usd_change=2.5
    )
    
    pool_details = PoolDetails(
        id="0x88e6a0c2ddd26feeb64f039a2c41296fcb3f5640",
        chain="ethereum",
        dex_id="uniswap_v3",
        dex_name="Uniswap V3",
        tokens=[token1, token2],
        last_price_usd=1800.0,
        volume_usd=1000000.0,
        hour1=time_metrics,
        hour24=time_metrics,
        day=time_metrics
    )
    
    client.pools.get_details = MagicMock(return_value=pool_details)
    
    # Mock OHLCV data
    ohlcv_record = OHLCVRecord(
        time=int(datetime.now().timestamp()),
        open=1700.0,
        high=1850.0,
        low=1650.0,
        close=1800.0,
        volume=500000.0
    )
    
    client.pools.get_ohlcv = MagicMock(return_value=[ohlcv_record])
    
    # Mock transactions
    transaction = Transaction(
        tx_hash="0x123456789abcdef",
        block_number=12345678,
        timestamp=int(datetime.now().timestamp()),
        type="swap",
        amount_usd=1000.0
    )
    
    transactions_response = TransactionsResponse(
        transactions=[transaction],
        page_info=None
    )
    
    client.pools.get_transactions = MagicMock(return_value=transactions_response)
    
    # Mock Tokens API
    token_details = TokenDetails(
        id="0xa0b86991c6218b36c1d19d4a2e9eb0ce3606eb48",
        name="USD Coin",
        symbol="USDC",
        decimals=6,
        chain="ethereum",
        price_usd=1.0,
        market_cap_usd=27000000000.0
    )
    
    client.tokens.get_details = MagicMock(return_value=token_details)
    client.tokens.get_pools = MagicMock(return_value=pools_response)
    
    # Mock Search API
    search_result = SearchResult(
        tokens=[token_details],
        pools=[pool],
        dexes=[Dex(id="uniswap_v3", name="Uniswap V3", url="https://uniswap.org")]
    )
    
    client.search.search = MagicMock(return_value=search_result)
    
    return client 
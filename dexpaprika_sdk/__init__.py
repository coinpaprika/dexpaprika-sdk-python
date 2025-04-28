"""
DexPaprika SDK for Python
~~~~~~~~~~~~~~~~~~~~~~~~~

A Python client library for the DexPaprika API,
providing access to token, pool, and DEX data
across multiple blockchain networks.

:copyright: (c) 2024 CoinPaprika
:license: MIT, see LICENSE for more details.
"""

from .client import DexPaprikaClient
# Import models for easier access
from .models import (
    Network, Dex, DexesResponse,
    Token, Pool, PoolsResponse, TimeIntervalMetrics,
    PoolDetails, OHLCVRecord, Transaction, TransactionsResponse,
    TokenSummary, TokenDetails,
    DexInfo, SearchResult,
    Stats
)

__version__ = "0.2.0"
__all__ = [
    "DexPaprikaClient",
    # Models
    "Network", "Dex", "DexesResponse",
    "Token", "Pool", "PoolsResponse", "TimeIntervalMetrics",
    "PoolDetails", "OHLCVRecord", "Transaction", "TransactionsResponse",
    "TokenSummary", "TokenDetails",
    "DexInfo", "SearchResult",
    "Stats"
]

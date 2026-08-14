from pydantic import BaseModel, ConfigDict, Field
from typing import List, Optional, Dict, Any, Union

from .base import PaginatedResponse


class Token(BaseModel):
    # token info

    id: str = Field(...)
    name: str = Field(...)
    symbol: str = Field(...)
    chain: str = Field(...)
    decimals: int = Field(...)
    added_at: str = Field(...)
    fdv: Optional[float] = Field(None)
    total_supply: Optional[float] = Field(None)
    description: Optional[str] = Field(None)
    website: Optional[str] = Field(None)
    explorer: Optional[str] = Field(None)
    type: Optional[str] = Field(None)
    status: Optional[str] = Field(None)
    has_image: Optional[bool] = Field(None)


class Pool(BaseModel):
    # pool info

    id: str = Field(...)
    dex_id: str = Field(...)
    dex_name: str = Field(...)
    chain: str = Field(...)
    volume_usd: float = Field(...)
    created_at: str = Field(...)
    created_at_block_number: int = Field(...)
    transactions: int = Field(...)
    price_usd: float = Field(...)
    last_price_change_usd_5m: Optional[float] = Field(None)
    last_price_change_usd_1h: Optional[float] = Field(None)
    last_price_change_usd_24h: Optional[float] = Field(None)
    fee: Optional[float] = Field(None)
    tokens: List[Token] = Field(...)
    volume_usd_7d: Optional[float] = Field(None)
    liquidity_usd: Optional[float] = Field(None)


class PoolsResponse(PaginatedResponse[Pool]):
    # pools list response
    pools: List[Pool] = Field(...)


class TimeIntervalMetrics(BaseModel):
    # time metrics
    
    last_price_usd_change: float = Field(...)
    volume_usd: float = Field(...)
    buy_usd: float = Field(...)
    sell_usd: float = Field(...)
    sells: int = Field(...)
    buys: int = Field(...)
    txns: int = Field(...)


class PoolDetails(BaseModel):
    # detailed pool info
    
    id: str = Field(...)
    created_at_block_number: int = Field(...)
    chain: str = Field(...)
    created_at: str = Field(...)
    factory_id: str = Field(...)
    dex_id: str = Field(...)
    dex_name: str = Field(...)
    tokens: List[Token] = Field(...)
    last_price: float = Field(...)
    last_price_usd: float = Field(...)
    fee: Optional[float] = Field(None)
    price_time: str = Field(...)
    
    # time intervals
    day: TimeIntervalMetrics = Field(..., alias="24h")
    hour6: Optional[TimeIntervalMetrics] = Field(None, alias="6h")
    hour1: Optional[TimeIntervalMetrics] = Field(None, alias="1h")
    minute30: Optional[TimeIntervalMetrics] = Field(None, alias="30m")
    minute15: Optional[TimeIntervalMetrics] = Field(None, alias="15m")
    minute5: Optional[TimeIntervalMetrics] = Field(None, alias="5m")

    model_config = ConfigDict(populate_by_name=True)


class OHLCVRecord(BaseModel):
    # price history data
    
    time_open: str = Field(...)
    time_close: str = Field(...)
    open: float = Field(...)
    high: float = Field(...)
    low: float = Field(...)
    close: float = Field(...)
    volume: int = Field(...)


class Transaction(BaseModel):
    # tx info
    
    id: str = Field(...)
    log_index: int = Field(...)
    transaction_index: int = Field(...)
    pool_id: str = Field(...)
    sender: str = Field(...)
    recipient: Union[str, int] = Field(...)
    token_0: str = Field(...)
    token_1: str = Field(...)
    amount_0: Union[str, int, float] = Field(...)
    amount_1: Union[str, int, float] = Field(...)
    created_at_block_number: int = Field(...)


class TransactionsResponse(PaginatedResponse[Transaction]):
    # txs list response
    transactions: List[Transaction] = Field(...)


class PoolSearchToken(BaseModel):
    """Lightweight token reference returned inside /pools/search results.

    Read off the wire on 2026-08-05: each entry carries ``id``, ``chain`` and
    ``has_image`` only. It is not the full Token model used by the pool detail
    endpoint. ``name`` and ``symbol`` are kept as optional fields for callers
    written against older responses; they come back as None today, so resolve
    symbols with ``client.tokens.get_details(chain, id)`` when you need them.
    """

    id: str = Field(...)
    chain: Optional[str] = Field(None)
    has_image: Optional[bool] = Field(None)
    name: Optional[str] = Field(None)
    symbol: Optional[str] = Field(None)


class PoolSearchResult(BaseModel):
    """A pool item from the unified /networks/{network}/pools/search endpoint.

    Replaces the old pools-list and pools/filter shapes. ``id`` is the pool
    address, volume is broken out by timeframe, transactions is
    ``transactions_24h`` and price changes are percentages. Metric fields are
    optional so a future shape tweak can't break deserialization.
    """

    id: str = Field(...)  # pool address
    chain: str = Field(...)
    dex_id: Optional[str] = Field(None)
    dex_name: Optional[str] = Field(None)
    fee: Optional[float] = Field(None)
    created_at: Optional[str] = Field(None)
    created_at_block_number: Optional[int] = Field(None)
    volume_usd_24h: Optional[float] = Field(None)
    volume_usd_7d: Optional[float] = Field(None)
    volume_usd_30d: Optional[float] = Field(None)
    liquidity_usd: Optional[float] = Field(None)
    transactions_24h: Optional[int] = Field(None)
    price_usd: Optional[float] = Field(None)
    price_change_percentage_5m: Optional[float] = Field(None)
    price_change_percentage_1h: Optional[float] = Field(None)
    price_change_percentage_6h: Optional[float] = Field(None)
    price_change_percentage_24h: Optional[float] = Field(None)
    tokens: List[PoolSearchToken] = Field(default_factory=list)


class PoolSearchResponse(BaseModel):
    """Cursor-paginated response from /networks/{network}/pools/search.

    The search endpoints are cursor-based: there is no ``page_info``. Rows are
    under ``results`` with ``has_next_page`` / ``next_cursor`` for pagination.
    """

    results: List[PoolSearchResult] = Field(default_factory=list)
    has_next_page: bool = Field(False)
    next_cursor: Optional[str] = Field(None)
    query: Optional[Dict[str, Any]] = Field(None)

    @property
    def pools(self) -> List[PoolSearchResult]:
        """Backward-compatible accessor: the old list endpoints returned rows
        under ``pools``. The search endpoint returns them under ``results``."""
        return self.results


# Backward-compatible aliases. These names referred to the now-removed /pools
# and /pools/filter response shapes; they now point at the unified search models.
FilteredPool = PoolSearchResult
PoolFilterResponse = PoolSearchResponse
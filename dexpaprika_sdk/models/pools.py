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


class FilteredPool(BaseModel):
    """Pool data from the pool filter endpoint (/networks/{id}/pools/filter).

    The filter endpoint returns a different shape than the pools list: volume is
    broken out by timeframe (volume_usd_24h / _7d / _30d) and liquidity_usd is
    included, instead of the single flat ``volume_usd`` the list endpoint returns.
    Metric fields are optional so a future shape tweak can't break deserialization.
    """

    id: str = Field(...)
    dex_id: str = Field(...)
    dex_name: str = Field(...)
    chain: str = Field(...)
    tokens: List[Token] = Field(...)
    created_at: Optional[str] = Field(None)
    created_at_block_number: Optional[int] = Field(None)
    transactions: Optional[int] = Field(None)
    price_usd: Optional[float] = Field(None)
    volume_usd_24h: Optional[float] = Field(None)
    volume_usd_7d: Optional[float] = Field(None)
    volume_usd_30d: Optional[float] = Field(None)
    liquidity_usd: Optional[float] = Field(None)
    last_price_change_usd_5m: Optional[float] = Field(None)
    last_price_change_usd_1h: Optional[float] = Field(None)
    last_price_change_usd_24h: Optional[float] = Field(None)
    fee: Optional[float] = Field(None)


class PoolFilterResponse(PaginatedResponse[FilteredPool]):
    # pool filter response (uses 'results' key)
    results: List[FilteredPool] = Field(...)


# --- Advanced pool search (/frontend/v1/pools) ---------------------------------
#
# These models back pools.advanced_search(). The frontend endpoint returns a
# richer shape than the public /pools list: cursor pagination, per-timeframe
# volume, and (with detailed=True) full token metadata plus per-timeframe metric
# blocks. Every field below is optional/nullable on purpose: in basic mode a
# token carries only id/chain/has_image, and even in detailed mode the API drops
# fields like fdv on some tokens. Hard-requiring any of these is exactly the bug
# that broke the #40 filter models, so we never do it here.


class TokenTimeframeMetrics(BaseModel):
    """Per-timeframe trading metrics for a token (detailed=True only).

    Keyed in the response by timeframe ("1m", "5m", ... "24h"). All fields are
    optional because the API may omit any of them; last_price_usd_change in
    particular is frequently null.
    """

    volume_usd: Optional[float] = Field(None)
    buys: Optional[int] = Field(None)
    sells: Optional[int] = Field(None)
    txns: Optional[int] = Field(None)
    last_price_usd_change: Optional[float] = Field(None)


class SearchToken(BaseModel):
    """A token inside an advanced-search pool row.

    In basic mode only id/chain/has_image are present. With detailed=True the
    API adds name, symbol, decimals, supply/fdv, links, and the timeframe metric
    blocks below. Unknown extra keys are tolerated so a backend addition can't
    break deserialization.
    """

    id: Optional[str] = Field(None)
    chain: Optional[str] = Field(None)
    has_image: Optional[bool] = Field(None)

    # detailed=True adds these
    name: Optional[str] = Field(None)
    symbol: Optional[str] = Field(None)
    status: Optional[str] = Field(None)
    decimals: Optional[int] = Field(None)
    added_at: Optional[str] = Field(None)
    total_supply: Optional[float] = Field(None)
    fdv: Optional[float] = Field(None)
    description: Optional[str] = Field(None)
    website: Optional[str] = Field(None)

    # per-timeframe metric blocks (detailed=True). Aliased because Python
    # attributes cannot start with a digit.
    minute1: Optional[TokenTimeframeMetrics] = Field(None, alias="1m")
    minute5: Optional[TokenTimeframeMetrics] = Field(None, alias="5m")
    minute15: Optional[TokenTimeframeMetrics] = Field(None, alias="15m")
    minute30: Optional[TokenTimeframeMetrics] = Field(None, alias="30m")
    hour1: Optional[TokenTimeframeMetrics] = Field(None, alias="1h")
    hour6: Optional[TokenTimeframeMetrics] = Field(None, alias="6h")
    hour24: Optional[TokenTimeframeMetrics] = Field(None, alias="24h")

    model_config = ConfigDict(populate_by_name=True, extra="allow")


class PoolRow(BaseModel):
    """A single pool row from the advanced-search endpoint.

    Unlike the public list (single flat volume_usd) this row carries volume split
    by timeframe (24h/7d/30d), liquidity, and 5m/1h/24h price-change percentages.
    Only id is treated as effectively always present; everything else is optional
    so a partial row never breaks the whole response.
    """

    id: str = Field(...)
    dex_id: Optional[str] = Field(None)
    dex_name: Optional[str] = Field(None)
    chain: Optional[str] = Field(None)
    fee: Optional[float] = Field(None)
    created_at: Optional[str] = Field(None)
    created_at_block_number: Optional[int] = Field(None)
    price_usd: Optional[float] = Field(None)
    transactions_24h: Optional[int] = Field(None)
    volume_usd_24h: Optional[float] = Field(None)
    volume_usd_7d: Optional[float] = Field(None)
    volume_usd_30d: Optional[float] = Field(None)
    liquidity_usd: Optional[float] = Field(None)
    price_change_percentage_5m: Optional[float] = Field(None)
    price_change_percentage_1h: Optional[float] = Field(None)
    price_change_percentage_24h: Optional[float] = Field(None)
    tokens: List[SearchToken] = Field(default_factory=list)

    model_config = ConfigDict(extra="allow")


class PoolSearchResponse(BaseModel):
    """Response from the advanced pool search endpoint.

    Cursor-paginated: when has_next_page is True, pass next_cursor back as the
    ``cursor`` argument to fetch the next page (this endpoint is NOT page-based).
    ``query`` echoes the wire params the backend actually applied (order_by/sort),
    so it is kept as a permissive dict rather than a typed model.
    """

    results: List[PoolRow] = Field(default_factory=list)
    has_next_page: Optional[bool] = Field(None)
    next_cursor: Optional[str] = Field(None)
    query: Optional[Dict[str, Any]] = Field(None)

    model_config = ConfigDict(extra="allow")
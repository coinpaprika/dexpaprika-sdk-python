from pydantic import BaseModel, Field
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

    class Config:
        populate_by_name = True


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
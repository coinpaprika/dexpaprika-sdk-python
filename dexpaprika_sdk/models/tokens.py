from pydantic import BaseModel, ConfigDict, Field
from typing import List, Optional, Dict, Any

from .base import PaginatedResponse
from .pools import TimeIntervalMetrics, Pool


class TokenSummary(BaseModel):
    """Summary metrics for a token."""
    
    price_usd: float = Field(..., description="Current price in USD")
    fdv: Optional[float] = Field(None, description="Fully diluted valuation (may be None for some chains like Solana)")
    liquidity_usd: float = Field(..., description="Total liquidity in USD")
    pools: Optional[int] = Field(None, description="Number of pools containing the token")
    
    # Time interval metrics
    day: Optional[TimeIntervalMetrics] = Field(None, alias="24h", description="Metrics for the last 24 hours")
    hour6: Optional[TimeIntervalMetrics] = Field(None, alias="6h", description="Metrics for the last 6 hours")
    hour1: Optional[TimeIntervalMetrics] = Field(None, alias="1h", description="Metrics for the last hour")
    minute30: Optional[TimeIntervalMetrics] = Field(None, alias="30m", description="Metrics for the last 30 minutes")
    minute15: Optional[TimeIntervalMetrics] = Field(None, alias="15m", description="Metrics for the last 15 minutes")
    minute5: Optional[TimeIntervalMetrics] = Field(None, alias="5m", description="Metrics for the last 5 minutes")
    minute1: Optional[TimeIntervalMetrics] = Field(None, alias="1m", description="Metrics for the last minute")

    model_config = ConfigDict(populate_by_name=True)


class TokenDetails(BaseModel):
    """Detailed information about a token."""
    
    id: str = Field(..., description="Token identifier or address")
    name: str = Field(..., description="Human-readable name of the token")
    symbol: str = Field(..., description="Token symbol")
    chain: str = Field(..., description="Network the token is on")
    decimals: int = Field(..., description="Decimal precision of the token")
    total_supply: Optional[float] = Field(None, description="Total supply of the token (may be None for some chains like Solana)")
    description: str = Field("", description="Token description")
    website: str = Field("", description="Token website URL")
    telegram: str = Field("", description="Official Telegram URL for the token/project")
    twitter: str = Field("", description="Official Twitter URL for the token/project")
    explorer: str = Field("", description="Token explorer URL")
    added_at: str = Field(..., description="When the token was added to the system")
    summary: Optional[TokenSummary] = Field(None, description="Token summary metrics")
    last_updated: Optional[str] = Field(None, description="When the token data was last updated")


class TokenDetailsLight(BaseModel):
    """Lightweight token details used in search results."""

    id: str = Field(..., description="Token identifier or address")
    name: str = Field(..., description="Human-readable name of the token")
    symbol: str = Field(..., description="Token symbol")
    chain: str = Field(..., description="Network the token is on")
    decimals: int = Field(..., description="Decimal precision of the token")
    total_supply: Optional[float] = Field(None, description="Total supply of the token (may be None for some chains like Solana)")
    description: str = Field("", description="Token description")
    website: str = Field("", description="Token website URL")
    telegram: str = Field("", description="Official Telegram URL for the token/project")
    twitter: str = Field("", description="Official Twitter URL for the token/project")
    explorer: str = Field("", description="Token explorer URL")
    added_at: Optional[str] = Field(None, description="When the token was added to the system")
    price_usd: Optional[float] = Field(None, description="Current price in USD")
    liquidity_usd: Optional[float] = Field(None, description="Total liquidity in USD")
    volume_usd: Optional[float] = Field(None, description="Trading volume in USD")
    price_usd_change: Optional[float] = Field(None, description="Price change in USD")
    type: Optional[str] = Field(None, description="Token type")
    status: Optional[str] = Field(None, description="Token status")


class TopTokenTimeMetrics(BaseModel):
    """Time interval metrics for top tokens (lighter than full TimeIntervalMetrics)."""

    volume_usd: float = Field(...)
    txns: int = Field(...)
    last_price_usd_change: Optional[float] = Field(None)
    buys: Optional[int] = Field(None)
    sells: Optional[int] = Field(None)


class TopToken(BaseModel):
    """Token data from the top tokens endpoint."""

    address: str = Field(...)
    name: str = Field(...)
    symbol: str = Field(...)
    chain: str = Field(...)
    decimals: int = Field(...)
    has_image: Optional[bool] = Field(None)
    price_usd: Optional[float] = Field(None)
    fdv: Optional[float] = Field(None)
    liquidity_usd: Optional[float] = Field(None)
    pools: Optional[int] = Field(None)

    # Time interval metrics
    day: Optional[TopTokenTimeMetrics] = Field(None, alias="24h")
    hour1: Optional[TopTokenTimeMetrics] = Field(None, alias="1h")
    minute5: Optional[TopTokenTimeMetrics] = Field(None, alias="5m")

    model_config = ConfigDict(populate_by_name=True)


class TopTokensResponse(PaginatedResponse):
    """Response from the top tokens endpoint."""
    tokens: List[TopToken] = Field(...)


class FilteredToken(BaseModel):
    """Token data from the token filter endpoint."""

    chain: str = Field(...)
    address: str = Field(...)
    price_usd: Optional[float] = Field(None)
    volume_usd_24h: Optional[float] = Field(None)
    volume_usd_7d: Optional[float] = Field(None)
    liquidity_usd: Optional[float] = Field(None)
    fdv_usd: Optional[float] = Field(None)
    txns_24h: Optional[int] = Field(None)
    created_at: Optional[str] = Field(None)


class TokenFilterResponse(PaginatedResponse):
    """Response from the token filter endpoint."""
    results: List[FilteredToken] = Field(...)


class TokenPrice(BaseModel):
    """Token price from the multi-prices endpoint."""

    chain: str = Field(...)
    id: str = Field(...)
    price_usd: Optional[float] = Field(None) 
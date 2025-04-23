from pydantic import BaseModel, Field
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

    class Config:
        populate_by_name = True


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
    explorer: str = Field("", description="Token explorer URL")
    added_at: Optional[str] = Field(None, description="When the token was added to the system")
    price_usd: Optional[float] = Field(None, description="Current price in USD")
    liquidity_usd: Optional[float] = Field(None, description="Total liquidity in USD")
    volume_usd: Optional[float] = Field(None, description="Trading volume in USD")
    price_usd_change: Optional[float] = Field(None, description="Price change in USD")
    type: Optional[str] = Field(None, description="Token type")
    status: Optional[str] = Field(None, description="Token status") 
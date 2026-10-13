from pydantic import BaseModel, Field
from typing import Any, Dict, List, Optional


class IndicatorDataPoint(BaseModel):
    """One computed value of a technical indicator.

    ``timestamp`` (RFC3339, candle open time) is always present. Which of the
    numeric fields are set depends on the indicator: rsi, ema and vwap carry
    ``value``; macd carries ``macd``, ``signal`` and ``histogram``; bbands
    carries ``upper``, ``middle`` and ``lower``. All are optional so a shape
    this SDK does not yet know about still parses.
    """

    timestamp: str = Field(...)
    value: Optional[float] = Field(None)
    macd: Optional[float] = Field(None)
    signal: Optional[float] = Field(None)
    histogram: Optional[float] = Field(None)
    upper: Optional[float] = Field(None)
    middle: Optional[float] = Field(None)
    lower: Optional[float] = Field(None)


class IndicatorResponse(BaseModel):
    """Response from GET .../pools/{address}/indicators or
    GET .../tokens/{address}/indicators.

    ``pool_address`` is present on the pool endpoint, ``token_address`` on the
    token endpoint; never both. ``parameters`` carries the parameters the API
    actually used to compute ``data``, including its own defaults for anything
    the caller left unset. ``data`` is oldest first, one item per completed
    candle; cursor-paginated like the OHLCV and search endpoints, through
    ``has_next_page`` and ``next_cursor``.
    """

    network: str = Field(...)
    pool_address: Optional[str] = Field(None)
    token_address: Optional[str] = Field(None)
    indicator: str = Field(...)
    interval: str = Field(...)
    parameters: Dict[str, Any] = Field(default_factory=dict)
    data: List[IndicatorDataPoint] = Field(default_factory=list)
    has_next_page: bool = Field(False)
    next_cursor: Optional[str] = Field(None)

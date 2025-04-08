from pydantic import BaseModel, Field
from typing import List, Optional

from .tokens import TokenDetailsLight
from .pools import Pool


class DexInfo(BaseModel):
    """Basic information about a DEX in search results."""
    
    id: str = Field(..., description="DEX identifier")
    dex_id: str = Field(..., description="DEX identifier (alternative)")
    dex_name: str = Field(..., description="DEX name")
    chain: str = Field(..., description="Network the DEX operates on")
    volume_usd_24h: float = Field(..., description="24-hour trading volume in USD")
    txns_24h: int = Field(..., description="Number of transactions in the last 24 hours")
    pools_count: int = Field(..., description="Number of pools in the DEX")
    protocol: str = Field(..., description="Protocol or underlying technology of the DEX")
    created_at: str = Field(..., description="When the DEX was created")


class SearchResult(BaseModel):
    """Search results across tokens, pools, and DEXes."""
    
    tokens: List[TokenDetailsLight] = Field([], description="Matching tokens")
    pools: List[Pool] = Field([], description="Matching pools")
    dexes: List[DexInfo] = Field([], description="Matching DEXes") 
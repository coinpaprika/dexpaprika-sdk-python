from pydantic import BaseModel, Field
from typing import List, Optional

from .base import PaginatedResponse, PageInfo


class Network(BaseModel):
    """Blockchain network information."""
    
    id: str = Field(..., description="Network identifier (e.g., 'ethereum', 'solana')")
    display_name: str = Field(..., description="Human-readable name for the network")


class Dex(BaseModel):
    """Decentralized exchange information."""
    
    id: Optional[str] = Field(None, description="DEX identifier")
    dex_name: str = Field(..., description="Name of the DEX")
    chain: str = Field(..., description="Network the DEX operates on")
    protocol: Optional[str] = Field(None, description="Protocol or underlying technology of the DEX")


class DexesResponse(PaginatedResponse[Dex]):
    """Response containing a list of DEXes."""
    
    dexes: List[Dex] = Field(..., description="List of DEXes") 
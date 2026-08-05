from pydantic import BaseModel, Field
from typing import List, Optional

from .base import PaginatedResponse, PageInfo


class Network(BaseModel):
    """Blockchain network information."""
    
    id: str = Field(..., description="Network identifier (e.g., 'ethereum', 'solana')")
    display_name: str = Field(..., description="Human-readable name for the network")


class Dex(BaseModel):
    """Decentralized exchange information.

    Field names follow GET /networks/{network}/dexes on the wire.
    """

    dex_id: str = Field(..., description="DEX identifier (e.g., 'uniswap_v3'). This is the value the /pools/search dex_name filter matches")
    dex_name: str = Field(..., description="Human-readable DEX name (e.g., 'Uniswap V3'). Not accepted by the /pools/search dex_name filter")
    chain: str = Field(..., description="Network the DEX operates on")
    protocol: Optional[str] = Field(None, description="Protocol or underlying technology of the DEX")
    volume_usd_24h: Optional[float] = Field(None, description="24-hour trading volume in USD")
    txns_24h: Optional[int] = Field(None, description="Number of transactions in the last 24 hours")
    pools_count: Optional[int] = Field(None, description="Number of pools indexed on this DEX")

    @property
    def id(self) -> str:
        """Backward-compatible alias for ``dex_id``.

        Earlier releases declared this field as ``id``, which never matched the
        wire and so was always ``None``. It now returns the real identifier.
        """
        return self.dex_id


class DexesResponse(PaginatedResponse[Dex]):
    """Response containing a list of DEXes."""
    
    dexes: List[Dex] = Field(..., description="List of DEXes") 
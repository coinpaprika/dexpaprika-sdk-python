from typing import List, Optional

from .base import BaseAPI
from ..models.networks import Network, DexesResponse


class NetworksAPI(BaseAPI):
    """API service for network-related endpoints."""
    
    def list(self) -> List[Network]:
        """
        Retrieve a list of all supported blockchain networks.
        
        Returns:
            List of Network objects
        """
        data = self._get("/networks")
        return [Network(**item) for item in data]
    
    def list_dexes(self, network_id: str, page: int = 0, limit: int = 10) -> DexesResponse:
        """
        Get a list of all available dexes on a specific network.
        
        Args:
            network_id: Network ID (e.g., "ethereum", "solana")
            page: Page number for pagination
            limit: Number of items per page
            
        Returns:
            Response containing a list of DEXes
        """
        params = {
            "page": page,
            "limit": limit,
        }
        data = self._get(f"/networks/{network_id}/dexes", params=params)
        return DexesResponse(**data) 
from typing import List, Optional, Set

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
            
        Raises:
            ValueError: If any parameter is invalid
        """
        # Validate parameters
        self._validate_required("network_id", network_id)
        self._validate_range("page", page, min_val=0)
        self._validate_range("limit", limit, min_val=1, max_val=100)
        
        params = {
            "page": page,
            "limit": limit,
        }
        data = self._get(f"/networks/{network_id}/dexes", params=params)
        return DexesResponse(**data) 
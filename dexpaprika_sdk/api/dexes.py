from typing import Optional

from .base import BaseAPI
from ..models.networks import DexesResponse


class DexesAPI(BaseAPI):
    """API service for DEX-related endpoints."""
    
    def list(self, network: str, page: int = 0, limit: int = 10) -> DexesResponse:
        """
        Get a list of available decentralized exchanges on a specific network.
        
        Args:
            network: Network ID (e.g., "ethereum", "solana")
            page: Page number for pagination
            limit: Number of items per page
            
        Returns:
            Response containing list of DEXes
        """
        params = {
            "page": page,
            "limit": limit
        }
        data = self._get(f"/networks/{network}/dexes", params=params)
        return DexesResponse(**data) 
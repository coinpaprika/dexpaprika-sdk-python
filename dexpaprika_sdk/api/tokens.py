from typing import Optional, Dict, Any, Set

from .base import BaseAPI
from ..models.tokens import TokenDetails
from ..models.pools import PoolsResponse
from ..utils.perf import track_perf


class TokensAPI(BaseAPI):
    """API service for token-related endpoints."""
    
    # Valid values for common parameters
    VALID_SORT_VALUES: Set[str] = {"asc", "desc"}
    VALID_ORDER_BY_VALUES: Set[str] = {"volume_usd", "price_usd", "transactions", "last_price_change_usd_24h", "created_at"}
    
    @track_perf
    def get_details(self, network_id: str, token_address: str) -> TokenDetails:
        """
        Get detailed information about a specific token on a network.
        
        Args:
            network_id: Network ID (e.g., "ethereum", "solana")
            token_address: Token address or identifier
            
        Returns:
            Detailed information about the token
            
        Raises:
            ValueError: If any parameter is invalid
        """
        # Validate parameters
        self._validate_required("network_id", network_id)
        self._validate_required("token_address", token_address)
        
        data = self._get(f"/networks/{network_id}/tokens/{token_address}")
        return TokenDetails(**data)
    
    @track_perf
    def get_pools(
        self, 
        network_id: str, 
        token_address: str, 
        page: int = 0, 
        limit: int = 10, 
        sort: str = "desc", 
        order_by: str = "volume_usd",
        address: Optional[str] = None,
    ) -> PoolsResponse:
        """
        Get a list of top liquidity pools for a specific token on a network.
        
        Args:
            network_id: Network ID (e.g., "ethereum", "solana")
            token_address: Token address or identifier
            page: Page number for pagination
            limit: Number of items per page
            sort: Sort order ("asc" or "desc")
            order_by: Field to order by ("volume_usd", "price_usd", "transactions", 
                     "last_price_change_usd_24h", "created_at")
            address: Filter pools that contain this additional token address
            
        Returns:
            Response containing a list of pools for the given token
            
        Raises:
            ValueError: If any parameter is invalid
        """
        # Validate parameters
        self._validate_required("network_id", network_id)
        self._validate_required("token_address", token_address)
        self._validate_range("page", page, min_val=0)
        self._validate_range("limit", limit, min_val=1, max_val=100)
        self._validate_enum("sort", sort, self.VALID_SORT_VALUES)
        self._validate_enum("order_by", order_by, self.VALID_ORDER_BY_VALUES)
        
        params = {
            "page": page,
            "limit": limit,
            "sort": sort,
            "order_by": order_by,
            "address": address,
        }
        params = self._clean_params(params)
        
        data = self._get(f"/networks/{network_id}/tokens/{token_address}/pools", params=params)
        
        # ensure pools exists
        if 'pools' not in data: data['pools'] = []
            
        return PoolsResponse(**data) 
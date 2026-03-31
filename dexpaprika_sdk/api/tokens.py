from typing import Optional, Dict, Any, Set, List, Union

from .base import BaseAPI
from ..models.tokens import (
    TokenDetails, TopTokensResponse, TokenFilterResponse, TokenPrice,
)
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
        reorder: Optional[bool] = None,
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
            reorder: If true, reorders the pool so that the specified token becomes 
                    the primary token for all metrics and calculations. Useful when 
                    the provided token is not the first token in the pool.
            
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
            "reorder": reorder,
        }
        params = self._clean_params(params)
        
        data = self._get(f"/networks/{network_id}/tokens/{token_address}/pools", params=params)

        # ensure pools exists
        if 'pools' not in data: data['pools'] = []

        return PoolsResponse(**data)

    @track_perf
    def get_top(
        self,
        network_id: str,
        page: int = 1,
        limit: int = 10,
        order_by: str = "volume_24h",
        sort: str = "desc",
    ) -> TopTokensResponse:
        """
        Get top tokens on a network ranked by volume, price, liquidity, or other metrics.

        Args:
            network_id: Network ID (e.g., "ethereum", "solana")
            page: Page number for pagination (1-indexed)
            limit: Number of items per page (max 100)
            order_by: Field to order by (e.g., "volume_24h", "price_usd", "liquidity_usd", "txns_24h")
            sort: Sort direction ("asc" or "desc")

        Returns:
            Top tokens with pagination info

        Raises:
            ValueError: If any parameter is invalid
        """
        self._validate_required("network_id", network_id)
        self._validate_range("page", page, min_val=1)
        self._validate_range("limit", limit, min_val=1, max_val=100)
        self._validate_enum("sort", sort, self.VALID_SORT_VALUES)

        params = {
            "page": page,
            "limit": limit,
            "order_by": order_by,
            "sort": sort,
        }
        params = self._clean_params(params)

        data = self._get(f"/networks/{network_id}/tokens/top", params=params)

        if 'tokens' not in data:
            data['tokens'] = []

        return TopTokensResponse(**data)

    @track_perf
    def filter(
        self,
        network_id: str,
        page: int = 1,
        limit: int = 10,
        sort_by: str = "volume_24h",
        sort_dir: str = "desc",
        volume_24h_min: Optional[float] = None,
        volume_24h_max: Optional[float] = None,
        liquidity_usd_min: Optional[float] = None,
        fdv_min: Optional[float] = None,
        fdv_max: Optional[float] = None,
        txns_24h_min: Optional[int] = None,
        created_after: Optional[Union[int, str]] = None,
        created_before: Optional[Union[int, str]] = None,
    ) -> TokenFilterResponse:
        """
        Filter tokens on a network by volume, liquidity, FDV, transactions, and creation date.

        Args:
            network_id: Network ID (e.g., "ethereum", "solana")
            page: Page number for pagination (1-indexed)
            limit: Number of items per page (max 100)
            sort_by: Field to sort by (e.g., "volume_24h", "liquidity_usd", "fdv", "txns_24h")
            sort_dir: Sort direction ("asc" or "desc")
            volume_24h_min: Minimum 24h volume in USD
            volume_24h_max: Maximum 24h volume in USD
            liquidity_usd_min: Minimum liquidity in USD
            fdv_min: Minimum fully diluted valuation in USD
            fdv_max: Maximum fully diluted valuation in USD
            txns_24h_min: Minimum number of transactions in 24h
            created_after: Only tokens created after this time (Unix timestamp)
            created_before: Only tokens created before this time (Unix timestamp)

        Returns:
            Filtered tokens with pagination info

        Raises:
            ValueError: If any parameter is invalid
        """
        self._validate_required("network_id", network_id)
        self._validate_range("page", page, min_val=1)
        self._validate_range("limit", limit, min_val=1, max_val=100)
        self._validate_enum("sort_dir", sort_dir, self.VALID_SORT_VALUES)

        params = {
            "page": page,
            "limit": limit,
            "sort_by": sort_by,
            "sort_dir": sort_dir,
            "volume_24h_min": volume_24h_min,
            "volume_24h_max": volume_24h_max,
            "liquidity_usd_min": liquidity_usd_min,
            "fdv_min": fdv_min,
            "fdv_max": fdv_max,
            "txns_24h_min": txns_24h_min,
            "created_after": created_after,
            "created_before": created_before,
        }
        params = self._clean_params(params)

        data = self._get(f"/networks/{network_id}/tokens/filter", params=params)

        if 'results' not in data:
            data['results'] = []

        return TokenFilterResponse(**data)

    @track_perf
    def get_multi_prices(
        self,
        network_id: str,
        tokens: List[str],
    ) -> List[TokenPrice]:
        """
        Get batch prices for multiple tokens on a network.

        Args:
            network_id: Network ID (e.g., "ethereum", "solana")
            tokens: List of token addresses (max 10)

        Returns:
            List of token prices

        Raises:
            ValueError: If any parameter is invalid
        """
        self._validate_required("network_id", network_id)
        if not tokens or len(tokens) == 0:
            raise ValueError("tokens list is required and must not be empty")
        if len(tokens) > 10:
            raise ValueError("tokens list must contain at most 10 addresses")

        params = {"tokens": ",".join(tokens)}

        data = self._get(f"/networks/{network_id}/multi/prices", params=params)
        return [TokenPrice(**item) for item in data]
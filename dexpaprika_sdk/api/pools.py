from typing import List, Optional, Dict, Any, Set

from .base import BaseAPI
from ..models.pools import (
    PoolsResponse, PoolDetails, OHLCVRecord, TransactionsResponse
)


class PoolsAPI(BaseAPI):
    """API service for pool-related endpoints."""
    
    # Valid values for common parameters
    VALID_SORT_VALUES: Set[str] = {"asc", "desc"}
    VALID_ORDER_BY_VALUES: Set[str] = {"volume_usd", "price_usd", "transactions", "last_price_change_usd_24h", "created_at"}
    VALID_INTERVAL_VALUES: Set[str] = {"1m", "5m", "10m", "15m", "30m", "1h", "6h", "12h", "24h"}
    
    def list(
        self, 
        page: int = 0, 
        limit: int = 10, 
        sort: str = "desc", 
        order_by: str = "volume_usd"
    ) -> PoolsResponse:
        """
        Get a list of top pools across all networks.
        
        Args:
            page: Page number for pagination
            limit: Number of items per page
            sort: Sort order ("asc" or "desc")
            order_by: Field to order by ("volume_usd", "price_usd", etc.)
            
        Returns:
            Response containing a list of pools
            
        Raises:
            ValueError: If any parameter is invalid
        """
        # Validate parameters
        self._validate_range("page", page, min_val=0)
        self._validate_range("limit", limit, min_val=1, max_val=100)
        self._validate_enum("sort", sort, self.VALID_SORT_VALUES)
        self._validate_enum("order_by", order_by, self.VALID_ORDER_BY_VALUES)
        
        # Get top pools
        params = {"page": page, "limit": limit, "sort": sort, "order_by": order_by}
        data = self._get("/pools", params=params)
        
        # ensure pools exists
        if 'pools' not in data: data['pools'] = []
            
        return PoolsResponse(**data)
    
    def list_by_network(
        self, 
        network_id: str, 
        page: int = 0, 
        limit: int = 10, 
        sort: str = "desc", 
        order_by: str = "volume_usd"
    ) -> PoolsResponse:
        """
        Get a list of pools on a specific network.
        
        Args:
            network_id: Network ID (e.g., "ethereum", "solana")
            page: Page number for pagination
            limit: Number of items per page
            sort: Sort order ("asc" or "desc")
            order_by: Field to order by ("volume_usd", "price_usd", etc.)
            
        Returns:
            Response containing a list of pools
            
        Raises:
            ValueError: If any parameter is invalid
        """
        # Validate parameters
        self._validate_required("network_id", network_id)
        self._validate_range("page", page, min_val=0)
        self._validate_range("limit", limit, min_val=1, max_val=100)
        self._validate_enum("sort", sort, self.VALID_SORT_VALUES)
        self._validate_enum("order_by", order_by, self.VALID_ORDER_BY_VALUES)
        
        # Get network pools
        params = {"page": page, "limit": limit, "sort": sort, "order_by": order_by}
        data = self._get(f"/networks/{network_id}/pools", params=params)
        
        # ensure pools exists
        if 'pools' not in data: data['pools'] = []
            
        return PoolsResponse(**data)
    
    def list_by_dex(
        self, 
        network_id: str, 
        dex_id: str, 
        page: int = 0, 
        limit: int = 10, 
        sort: str = "desc", 
        order_by: str = "volume_usd"
    ) -> PoolsResponse:
        """
        Get a list of pools for a specific DEX on a network.
        
        Args:
            network_id: Network ID (e.g., "ethereum", "solana")
            dex_id: DEX ID (e.g., "uniswap_v3")
            page: Page number for pagination
            limit: Number of items per page
            sort: Sort order ("asc" or "desc")
            order_by: Field to order by ("volume_usd", "price_usd", etc.)
            
        Returns:
            Response containing a list of pools
            
        Raises:
            ValueError: If any parameter is invalid
        """
        # Validate parameters
        self._validate_required("network_id", network_id)
        self._validate_required("dex_id", dex_id)
        self._validate_range("page", page, min_val=0)
        self._validate_range("limit", limit, min_val=1, max_val=100)
        self._validate_enum("sort", sort, self.VALID_SORT_VALUES)
        self._validate_enum("order_by", order_by, self.VALID_ORDER_BY_VALUES)
        
        # Get dex pools
        params = {"page": page, "limit": limit, "sort": sort, "order_by": order_by}
        data = self._get(f"/networks/{network_id}/dexes/{dex_id}/pools", params=params)
        
        # ensure pools exists
        if 'pools' not in data: data['pools'] = []
            
        return PoolsResponse(**data)
    
    def get_details(
        self, 
        network_id: str, 
        pool_address: str, 
        inversed: bool = False
    ) -> PoolDetails:
        """
        Get detailed information about a specific pool.
        
        Args:
            network_id: Network ID (e.g., "ethereum", "solana")
            pool_address: Pool address or identifier
            inversed: Whether to invert the price ratio
            
        Returns:
            Detailed pool information
            
        Raises:
            ValueError: If any parameter is invalid
        """
        # Validate parameters
        self._validate_required("network_id", network_id)
        self._validate_required("pool_address", pool_address)
        
        # Get pool details
        params = {"inversed": "true" if inversed else None}
        params = self._clean_params(params)
        
        data = self._get(f"/networks/{network_id}/pools/{pool_address}", params=params)
        return PoolDetails(**data)
    
    def get_ohlcv(
        self, 
        network_id: str, 
        pool_address: str, 
        start: str, 
        end: Optional[str] = None, 
        limit: int = 1, 
        interval: str = "24h", 
        inversed: bool = False
    ) -> List[OHLCVRecord]:
        """
        Get OHLCV (Open-High-Low-Close-Volume) data for a specific pool.
        
        Args:
            network_id: Network ID (e.g., "ethereum", "solana")
            pool_address: Pool address or identifier
            start: Start time for historical data (ISO-8601, yyyy-mm-dd, or Unix timestamp)
            end: End time for historical data (max 1 year from start)
            limit: Number of data points to retrieve (max 366)
            interval: Interval granularity for OHLCV data (1m, 5m, 10m, 15m, 30m, 1h, 6h, 12h, 24h)
            inversed: Whether to invert the price ratio in OHLCV calculations
            
        Returns:
            List of OHLCV records
            
        Raises:
            ValueError: If any parameter is invalid
        """
        # Validate parameters
        self._validate_required("network_id", network_id)
        self._validate_required("pool_address", pool_address)
        self._validate_required("start", start)
        self._validate_range("limit", limit, min_val=1, max_val=366)
        self._validate_enum("interval", interval, self.VALID_INTERVAL_VALUES)
        
        # Get price history
        params = {
            "start": start,
            "end": end,
            "limit": limit,
            "interval": interval,
            "inversed": "true" if inversed else None,
        }
        params = self._clean_params(params)
        
        data = self._get(f"/networks/{network_id}/pools/{pool_address}/ohlcv", params=params)
        return [OHLCVRecord(**item) for item in data]
    
    def get_transactions(
        self, 
        network_id: str, 
        pool_address: str, 
        page: int = 0, 
        limit: int = 10, 
        cursor: Optional[str] = None
    ) -> TransactionsResponse:
        """
        Get transactions of a pool on a network.
        
        Args:
            network_id: Network ID (e.g., "ethereum", "solana")
            pool_address: Pool address or identifier
            page: Page number for pagination
            limit: Number of items per page
            cursor: Transaction ID used for cursor-based pagination
            
        Returns:
            Response containing a list of transactions
            
        Raises:
            ValueError: If any parameter is invalid
        """
        # Validate parameters
        self._validate_required("network_id", network_id)
        self._validate_required("pool_address", pool_address)
        self._validate_range("page", page, min_val=0)
        self._validate_range("limit", limit, min_val=1, max_val=100)
        
        # Get txs
        params = {"page": page, "limit": limit, "cursor": cursor}
        params = self._clean_params(params)
        
        data = self._get(f"/networks/{network_id}/pools/{pool_address}/transactions", params=params)
        return TransactionsResponse(**data) 
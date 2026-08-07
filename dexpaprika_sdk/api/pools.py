from typing import List, Optional, Dict, Any, Set, Union
import warnings

from .base import BaseAPI, map_pool_sort_field, map_filter_params, POOL_FILTER_PARAM_MAP
from ..models.pools import (
    PoolsResponse, PoolDetails, OHLCVRecord, TransactionsResponse,
    PoolSearchResponse,
)


class PoolsAPI(BaseAPI):
    """API service for pool-related endpoints."""

    # Valid values for common parameters
    VALID_SORT_VALUES: Set[str] = {"asc", "desc"}
    # order_by for the still-valid DEX pools endpoint (/dexes/{dex}/pools).
    VALID_ORDER_BY_VALUES: Set[str] = {"volume_usd", "price_usd", "transactions", "last_price_change_usd_24h", "created_at"}
    VALID_INTERVAL_VALUES: Set[str] = {"1m", "5m", "10m", "15m", "30m", "1h", "6h", "12h", "24h"}
    
    def list(
        self,
        page: int = 0,
        limit: int = 10,
        sort: str = "desc",
        order_by: str = "volume_usd",
        cursor: Optional[str] = None,
    ) -> PoolSearchResponse:
        """
        DEPRECATED: Get a list of top pools across all networks.

        This method is deprecated due to API changes. The global /pools endpoint
        has been removed. Use list_by_network(network_id, ...) instead.

        For backward compatibility, this method now defaults to the Ethereum
        network (via /networks/ethereum/pools/search).

        Args:
            page: Accepted for backward compatibility. The search endpoint is
                cursor-paginated, so this value is ignored for the request.
            limit: Number of items per page
            sort: Sort order ("asc" or "desc")
            order_by: Field to order by (legacy values such as "volume_usd" are
                mapped to canonical search fields automatically)
            cursor: Cursor for cursor-based pagination

        Returns:
            Cursor-paginated pool search response

        Raises:
            ValueError: If any parameter is invalid

        Migration Examples:
            # Before (deprecated):
            pools = client.pools.list()

            # After (recommended):
            pools = client.pools.list_by_network('ethereum')
            pools = client.pools.list_by_network('solana')
        """
        # Issue deprecation warning
        warnings.warn(
            "The pools.list() method is deprecated. The global /pools endpoint has been "
            "removed. Use pools.list_by_network(network_id) instead. "
            "This method now defaults to the Ethereum network for backward compatibility. "
            "Examples: client.pools.list_by_network('ethereum'), "
            "client.pools.list_by_network('solana')",
            DeprecationWarning,
            stacklevel=2
        )

        return self.list_by_network(
            "ethereum", page=page, limit=limit, sort=sort, order_by=order_by, cursor=cursor
        )

    def list_by_network(
        self,
        network_id: str,
        page: int = 0,
        limit: int = 10,
        sort: str = "desc",
        order_by: str = "volume_usd",
        cursor: Optional[str] = None,
    ) -> PoolSearchResponse:
        """
        Get a list of pools on a specific network via /pools/search.

        Args:
            network_id: Network ID (e.g., "ethereum", "solana")
            page: Accepted for backward compatibility. The search endpoint is
                cursor-paginated, so this value is ignored for the request.
            limit: Number of items per page
            sort: Sort order ("asc" or "desc")
            order_by: Field to order by (legacy values such as "volume_usd" are
                mapped to canonical search fields automatically). Pools can also
                be ordered by "price_change_percentage_24h", "..._6h", "..._1h"
                and "..._5m"; those windows exist on pools only.
            cursor: Cursor for cursor-based pagination

        Returns:
            Cursor-paginated pool search response

        Raises:
            ValueError: If any parameter is invalid
        """
        # Validate parameters
        self._validate_required("network_id", network_id)
        self._validate_range("page", page, min_val=0)
        self._validate_range("limit", limit, min_val=1, max_val=100)
        self._validate_enum("sort", sort, self.VALID_SORT_VALUES)

        # Build the cursor-based search request with canonical names.
        params = {
            "limit": limit,
            "order_by": map_pool_sort_field(order_by),
            "sort": sort,
            "cursor": cursor,
        }
        params = self._clean_params(params)

        data = self._get(f"/networks/{network_id}/pools/search", params=params)

        # ensure results exists
        if 'results' not in data:
            data['results'] = []

        return PoolSearchResponse(**data)
    
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
        cursor: Optional[str] = None,
        from_timestamp: Optional[int] = None,
        to_timestamp: Optional[int] = None
    ) -> TransactionsResponse:
        """
        Get transactions of a pool on a network.

        Args:
            network_id: Network ID (e.g., "ethereum", "solana")
            pool_address: Pool address or identifier
            page: Page number for pagination
            limit: Number of items per page
            cursor: Transaction ID used for cursor-based pagination
            from_timestamp: Filter transactions starting from this UNIX timestamp (inclusive). Results capped to last 7 days.
            to_timestamp: Filter transactions up to this UNIX timestamp (exclusive). Must be after from_timestamp.

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
        params = {"page": page, "limit": limit, "cursor": cursor, "from": from_timestamp, "to": to_timestamp}
        params = self._clean_params(params)

        data = self._get(f"/networks/{network_id}/pools/{pool_address}/transactions", params=params)
        return TransactionsResponse(**data)

    def filter(
        self,
        network_id: str,
        page: int = 1,
        limit: int = 10,
        sort_by: str = "volume_24h",
        sort_dir: str = "desc",
        volume_24h_min: Optional[float] = None,
        volume_24h_max: Optional[float] = None,
        volume_7d_min: Optional[float] = None,
        volume_7d_max: Optional[float] = None,
        liquidity_usd_min: Optional[float] = None,
        liquidity_usd_max: Optional[float] = None,
        txns_24h_min: Optional[int] = None,
        created_after: Optional[Union[int, str]] = None,
        created_before: Optional[Union[int, str]] = None,
        cursor: Optional[str] = None,
        price_change_percentage_24h_min: Optional[float] = None,
        price_change_percentage_24h_max: Optional[float] = None,
        price_change_percentage_6h_min: Optional[float] = None,
        price_change_percentage_6h_max: Optional[float] = None,
        price_change_percentage_1h_min: Optional[float] = None,
        price_change_percentage_1h_max: Optional[float] = None,
        price_change_percentage_5m_min: Optional[float] = None,
        price_change_percentage_5m_max: Optional[float] = None,
    ) -> PoolSearchResponse:
        """
        Filter pools on a network by volume, liquidity, transactions, price move, and creation date.

        Backed by /networks/{network}/pools/search. Legacy sort-field values and
        filter param names are mapped to the canonical search names automatically.

        The price-change bounds are percentages and negative values are
        meaningful: ``price_change_percentage_24h_max=-20`` selects pools down
        at least 20% on the day. Unknown filter names are ignored by the API and
        still answer 200 with a full unfiltered result set, so a bound that never
        reaches the wire looks like a working call that returns the wrong pools.

        Args:
            network_id: Network ID (e.g., "ethereum", "solana")
            page: Accepted for backward compatibility. The search endpoint is
                cursor-paginated, so this value is ignored for the request.
            limit: Number of items per page (max 100)
            sort_by: Field to sort by (e.g., "volume_24h", "liquidity_usd", "txns_24h",
                "created_at", "price_change_percentage_24h", "price_change_percentage_6h",
                "price_change_percentage_1h", "price_change_percentage_5m")
            sort_dir: Sort direction ("asc" or "desc")
            volume_24h_min: Minimum 24h volume in USD
            volume_24h_max: Maximum 24h volume in USD
            volume_7d_min: Minimum 7d volume in USD
            volume_7d_max: Maximum 7d volume in USD
            liquidity_usd_min: Minimum liquidity in USD
            liquidity_usd_max: Maximum liquidity in USD
            txns_24h_min: Minimum number of transactions in 24h
            created_after: Only pools created after this time (Unix timestamp)
            created_before: Only pools created before this time (Unix timestamp)
            cursor: Cursor for cursor-based pagination
            price_change_percentage_24h_min: Minimum 24h price change, in percent
            price_change_percentage_24h_max: Maximum 24h price change, in percent
            price_change_percentage_6h_min: Minimum 6h price change, in percent
            price_change_percentage_6h_max: Maximum 6h price change, in percent
            price_change_percentage_1h_min: Minimum 1h price change, in percent
            price_change_percentage_1h_max: Maximum 1h price change, in percent
            price_change_percentage_5m_min: Minimum 5m price change, in percent
            price_change_percentage_5m_max: Maximum 5m price change, in percent

        Returns:
            Cursor-paginated pool search response

        Raises:
            ValueError: If any parameter is invalid
        """
        self._validate_required("network_id", network_id)
        self._validate_range("page", page, min_val=1)
        self._validate_range("limit", limit, min_val=1, max_val=100)
        self._validate_enum("sort_dir", sort_dir, self.VALID_SORT_VALUES)

        # Sort + pagination, using canonical search param names.
        params = {
            "limit": limit,
            "order_by": map_pool_sort_field(sort_by),
            "sort": sort_dir,
            "cursor": cursor,
        }
        # Filter params, renamed from legacy to canonical search names.
        filters = {
            "volume_24h_min": volume_24h_min,
            "volume_24h_max": volume_24h_max,
            "volume_7d_min": volume_7d_min,
            "volume_7d_max": volume_7d_max,
            "liquidity_usd_min": liquidity_usd_min,
            "liquidity_usd_max": liquidity_usd_max,
            "txns_24h_min": txns_24h_min,
            "created_after": created_after,
            "created_before": created_before,
            # Pool-only price-change windows. These names are already canonical,
            # so they pass through map_filter_params untouched.
            "price_change_percentage_24h_min": price_change_percentage_24h_min,
            "price_change_percentage_24h_max": price_change_percentage_24h_max,
            "price_change_percentage_6h_min": price_change_percentage_6h_min,
            "price_change_percentage_6h_max": price_change_percentage_6h_max,
            "price_change_percentage_1h_min": price_change_percentage_1h_min,
            "price_change_percentage_1h_max": price_change_percentage_1h_max,
            "price_change_percentage_5m_min": price_change_percentage_5m_min,
            "price_change_percentage_5m_max": price_change_percentage_5m_max,
        }
        params.update(map_filter_params(filters, POOL_FILTER_PARAM_MAP))
        params = self._clean_params(params)

        data = self._get(f"/networks/{network_id}/pools/search", params=params)

        if 'results' not in data:
            data['results'] = []

        return PoolSearchResponse(**data)
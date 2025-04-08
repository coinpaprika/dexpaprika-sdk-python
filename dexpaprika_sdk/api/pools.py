from typing import List, Optional, Dict, Any

from .base import BaseAPI
from ..models.pools import (
    PoolsResponse, PoolDetails, OHLCVRecord, TransactionsResponse
)


class PoolsAPI(BaseAPI):
    # pool endpoints api
    
    def list(
        self, 
        page: int = 0, 
        limit: int = 10, 
        sort: str = "desc", 
        order_by: str = "volume_usd"
    ) -> PoolsResponse:
        # get top pools
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
        # get network pools
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
        # get dex pools
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
        # get pool details
        params = {"inversed": "true" if inversed else None}
        params = {k: v for k, v in params.items() if v is not None}
        
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
        # get price history
        params = {
            "start": start,
            "end": end,
            "limit": limit,
            "interval": interval,
            "inversed": "true" if inversed else None,
        }
        params = {k: v for k, v in params.items() if v is not None}
        
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
        # get txs
        params = {"page": page, "limit": limit, "cursor": cursor}
        params = {k: v for k, v in params.items() if v is not None}
        
        data = self._get(f"/networks/{network_id}/pools/{pool_address}/transactions", params=params)
        return TransactionsResponse(**data) 
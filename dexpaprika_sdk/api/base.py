from typing import Any, Dict, List, Optional, Union, TYPE_CHECKING

if TYPE_CHECKING:
    from ..client import DexPaprikaClient


class BaseAPI:
    """Base class for all API service classes."""

    def __init__(self, client: "DexPaprikaClient"):
        """
        Initialize a new API service.

        Args:
            client: The DexPaprika client instance
        """
        self.client = client
        self._cache = {}  # simple cache for perf
    
    def _get(self, endpoint: str, params: Optional[Dict[str, Any]] = None) -> Union[Dict[str, Any], List[Dict[str, Any]]]:
        """
        Make a GET request to the specified endpoint.

        Args:
            endpoint: API endpoint (e.g., "/networks")
            params: Query parameters

        Returns:
            Response data as a dictionary or list
        """
        # try cache first for common requests
        cache_key = f"{endpoint}:{str(params)}"
        if params is None and cache_key in self._cache:
            return self._cache[cache_key]
            
        result = self.client.get(endpoint, params=params)
        
        # cache if no params (these tend to be stable data)
        if params is None:
            self._cache[cache_key] = result
            
        return result
    
    def _post(self, endpoint: str, data: Dict[str, Any], params: Optional[Dict[str, Any]] = None) -> Union[Dict[str, Any], List[Dict[str, Any]]]:
        """
        Make a POST request to the specified endpoint.

        Args:
            endpoint: API endpoint
            data: Request body
            params: Query parameters

        Returns:
            Response data as a dictionary or list
        """
        return self.client.post(endpoint, data=data, params=params)
        
    def _clean_params(self, params: Dict[str, Any]) -> Dict[str, Any]:
        # clean none values from params
        return {k: v for k, v in params.items() if v is not None} 
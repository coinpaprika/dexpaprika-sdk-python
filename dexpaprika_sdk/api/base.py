from typing import Any, Dict, List, Optional, Union, TYPE_CHECKING, Callable, TypeVar, Set
import hashlib
import json
from datetime import datetime, timedelta

if TYPE_CHECKING:
    from ..client import DexPaprikaClient

T = TypeVar('T')

class CacheEntry:
    """Class representing a cached response with an expiration time."""
    
    def __init__(self, data: Any, expires_at: Optional[datetime] = None):
        """
        Initialize a new cache entry.
        
        Args:
            data: The data to cache
            expires_at: The time when the cache entry expires
        """
        self.data = data
        self.expires_at = expires_at
        
    def is_expired(self) -> bool:
        """
        Check if the cache entry has expired.
        
        Returns:
            True if the cache entry has expired, False otherwise
        """
        return self.expires_at is not None and datetime.now() > self.expires_at


class BaseAPI:
    """Base class for all API service classes."""

    def __init__(self, client: "DexPaprikaClient"):
        """
        Initialize a new API service.

        Args:
            client: The DexPaprika client instance
        """
        self.client = client
        self._cache: Dict[str, CacheEntry] = {}  # TTL-based cache
        
        # Default TTLs for different types of data
        self._cache_ttls = {
            "networks": timedelta(hours=24),  # Network list rarely changes
            "pools": timedelta(minutes=5),    # Pool data changes frequently
            "tokens": timedelta(minutes=10),  # Token data changes moderately
            "stats": timedelta(minutes=15),   # Stats change moderately
            "default": timedelta(minutes=5)   # Default TTL for other endpoints
        }
    
    def _get_cache_key(self, endpoint: str, params: Optional[Dict[str, Any]] = None) -> str:
        """
        Generate a unique cache key for the request.
        
        Args:
            endpoint: API endpoint
            params: Query parameters
            
        Returns:
            A unique cache key as a string
        """
        key_parts = [endpoint]
        if params:
            # Sort params to ensure consistent keys
            sorted_params = json.dumps(params, sort_keys=True)
            key_parts.append(sorted_params)
        
        key_string = ":".join(key_parts)
        return hashlib.md5(key_string.encode()).hexdigest()
    
    def _get_ttl(self, endpoint: str) -> timedelta:
        """
        Get the TTL for a specific endpoint.
        
        Args:
            endpoint: API endpoint
            
        Returns:
            The TTL as a timedelta
        """
        for key, ttl in self._cache_ttls.items():
            if key in endpoint:
                return ttl
        return self._cache_ttls["default"]
    
    def _get(
        self, 
        endpoint: str, 
        params: Optional[Dict[str, Any]] = None,
        skip_cache: bool = False,
        ttl: Optional[timedelta] = None
    ) -> Union[Dict[str, Any], List[Dict[str, Any]]]:
        """
        Make a GET request to the specified endpoint.

        Args:
            endpoint: API endpoint (e.g., "/networks")
            params: Query parameters
            skip_cache: Whether to skip the cache and force a fresh request
            ttl: Custom TTL for this request

        Returns:
            Response data as a dictionary or list
        """
        if skip_cache:
            return self.client.get(endpoint, params=params)
            
        cache_key = self._get_cache_key(endpoint, params)
        cache_entry = self._cache.get(cache_key)
        
        # Return cached data if valid
        if cache_entry and not cache_entry.is_expired():
            return cache_entry.data
            
        # Get fresh data
        result = self.client.get(endpoint, params=params)
        
        # Cache the result with appropriate TTL
        if ttl is None:
            ttl = self._get_ttl(endpoint)
            
        expires_at = datetime.now() + ttl
        self._cache[cache_key] = CacheEntry(result, expires_at)
            
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
        """Clean None values from params."""
        return {k: v for k, v in params.items() if v is not None}
    
    def _validate_required(self, param_name: str, value: Any) -> None:
        """
        Validate that a parameter is not None or empty.
        
        Args:
            param_name: Name of the parameter for error messages
            value: Value to validate
            
        Raises:
            ValueError: If the value is None or empty
        """
        if value is None or (isinstance(value, str) and value.strip() == ""):
            raise ValueError(f"{param_name} is required")
    
    def _validate_enum(self, param_name: str, value: str, valid_values: Set[str]) -> None:
        """
        Validate that a parameter is one of a set of valid values.
        
        Args:
            param_name: Name of the parameter for error messages
            value: Value to validate
            valid_values: Set of valid values
            
        Raises:
            ValueError: If the value is not one of the valid values
        """
        if value is None:
            return
            
        if value not in valid_values:
            raise ValueError(f"{param_name} must be one of: {', '.join(sorted(valid_values))}")
    
    def _validate_range(self, param_name: str, value: Union[int, float], min_val: Optional[Union[int, float]] = None, max_val: Optional[Union[int, float]] = None) -> None:
        """
        Validate that a numeric parameter is within a specified range.
        
        Args:
            param_name: Name of the parameter for error messages
            value: Value to validate
            min_val: Minimum allowed value (inclusive)
            max_val: Maximum allowed value (inclusive)
            
        Raises:
            ValueError: If the value is outside the specified range
        """
        if value is None:
            return
            
        if min_val is not None and value < min_val:
            raise ValueError(f"{param_name} must be at least {min_val}")
            
        if max_val is not None and value > max_val:
            raise ValueError(f"{param_name} must be at most {max_val}")
    
    def clear_cache(self, endpoint_prefix: Optional[str] = None) -> None:
        """
        Clear the cache, optionally only for endpoints with a specific prefix.
        
        Args:
            endpoint_prefix: Optional prefix to filter which cache entries to clear
        """
        if endpoint_prefix:
            # Get cache keys from the original endpoints that contain the prefix
            keys_to_remove = []
            for key in list(self._cache.keys()):
                cache_entry = self._cache[key]
                if endpoint_prefix in key:
                    keys_to_remove.append(key)
                    
            # Remove the entries
            for key in keys_to_remove:
                del self._cache[key]
        else:
            # Clear the entire cache
            self._cache.clear() 
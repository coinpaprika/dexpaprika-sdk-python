from typing import Any, Dict, List, Optional, Union, TYPE_CHECKING, Callable, TypeVar, Set

if TYPE_CHECKING:
    from ..client import DexPaprikaClient

T = TypeVar('T')

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
        """Clean None values from params."""
        return {k: v for k, v in params.items() if v is not None}
    
    def _validate_required(self, param_name: str, value: Any) -> None:
        """
        Validate that a required parameter is provided and not empty.
        
        Args:
            param_name: Name of the parameter for error messages
            value: Value to validate
            
        Raises:
            ValueError: If the parameter is None or empty string
        """
        if value is None or (isinstance(value, str) and not value.strip()):
            raise ValueError(f"{param_name} is required")
    
    def _validate_enum(self, param_name: str, value: Any, valid_values: Set[Any]) -> None:
        """
        Validate that a parameter value is in a set of valid values.
        
        Args:
            param_name: Name of the parameter for error messages
            value: Value to validate
            valid_values: Set of accepted values
            
        Raises:
            ValueError: If the value is not in the valid_values set
        """
        if value is not None and value not in valid_values:
            valid_str = ", ".join([str(v) for v in valid_values])
            raise ValueError(f"{param_name} must be one of: {valid_str}")
    
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
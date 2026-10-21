from typing import Any, Dict, List, Optional, Union, TYPE_CHECKING, Callable, TypeVar, Set
from collections import OrderedDict
import hashlib
import json
import re
from datetime import datetime, timedelta

if TYPE_CHECKING:
    from ..client import DexPaprikaClient

T = TypeVar('T')


# ---------------------------------------------------------------------------
# Unified search endpoint mappings
#
# DexPaprika removed the legacy /pools, /pools/filter, /tokens/top and
# /tokens/filter endpoints (now HTTP 410) in favour of /pools/search and
# /tokens/search. The search endpoints return HTTP 400 for the old sort-field
# values and the old filter param names, so everything must be mapped to the
# canonical names below. These are small, pure helpers shared by the pools and
# tokens API services.
# ---------------------------------------------------------------------------

# Sort-field values accepted as-is by /pools/search.
# The 6h / 1h / 5m price-change windows are pool-only. /tokens/search returns
# HTTP 400 for them and token rows carry no 5m field at all, so they must never
# be copied into TOKEN_SORT_CANONICAL below.
POOL_SORT_CANONICAL: Set[str] = {
    "volume_usd_24h", "volume_usd_7d", "volume_usd_30d", "liquidity_usd",
    "txns_24h", "created_at", "price_usd", "price_change_percentage_48h",
    "price_change_percentage_24h", "price_change_percentage_6h",
    "price_change_percentage_1h", "price_change_percentage_5m",
}

# Legacy sort-field value -> canonical /pools/search value.
POOL_SORT_FIELD_MAP: Dict[str, str] = {
    "volume_usd": "volume_usd_24h",
    "transactions": "txns_24h",
    "last_price_change_usd_24h": "price_change_percentage_24h",
    "volume_24h": "volume_usd_24h",
    "volume_7d": "volume_usd_7d",
    "volume_30d": "volume_usd_30d",
    "liquidity": "liquidity_usd",
}

# Sort-field values accepted as-is by /tokens/search.
# Deliberately shorter than POOL_SORT_CANONICAL: the 6h / 1h / 5m price-change
# windows are rejected here with HTTP 400. Adding them for symmetry would break
# every caller that used them.
TOKEN_SORT_CANONICAL: Set[str] = {
    "volume_usd_24h", "volume_usd_7d", "volume_usd_30d", "liquidity_usd",
    "txns_24h", "fdv_usd", "created_at", "price_change_percentage_24h",
}

# Legacy sort-field value -> canonical /tokens/search value.
# Note: /tokens/search returns 400 when ordering by price, so price_usd falls
# back to volume_usd_24h.
TOKEN_SORT_FIELD_MAP: Dict[str, str] = {
    "volume_24h": "volume_usd_24h",
    "txns": "txns_24h",
    "price_change": "price_change_percentage_24h",
    "fdv": "fdv_usd",
    "volume_7d": "volume_usd_7d",
    "volume_30d": "volume_usd_30d",
    "price_usd": "volume_usd_24h",
}

# Legacy filter param name -> canonical /pools/search query param name.
# Names not listed here (liquidity_usd_min, liquidity_usd_max, txns_24h_min,
# created_after, created_before, price_change_percentage_{24h,6h,1h,5m}_{min,max})
# are already canonical and pass through.
POOL_FILTER_PARAM_MAP: Dict[str, str] = {
    "volume_24h_min": "volume_usd_24h_min",
    "volume_24h_max": "volume_usd_24h_max",
    "volume_7d_min": "volume_usd_7d_min",
    "volume_7d_max": "volume_usd_7d_max",
}

# Legacy filter param name -> canonical /tokens/search query param name.
# Names not listed here (liquidity_usd_min, fdv_min, fdv_max, txns_24h_min,
# created_after, created_before, price_change_percentage_24h_min/_max) are
# already canonical and pass through.
#
# The filter side does not mirror the sort side. /tokens/search applies
# price_change_percentage_24h_min and _max. It answers 200 to the 6h, 1h and 5m
# bounds and then ignores them, so a caller who passed one would get a full
# unfiltered page that looks filtered. That is why tokens.filter() offers the
# 24h pair and refuses the other three outright.
TOKEN_FILTER_PARAM_MAP: Dict[str, str] = {
    "volume_24h_min": "volume_usd_24h_min",
    "volume_24h_max": "volume_usd_24h_max",
}


# Separators and anything a URL parser or the server could decode into one:
# slash, backslash, query and fragment marks, percent escapes, whitespace and
# control characters. Ids the API returns do not contain these; Sui and Aptos
# ids with "::" and TON addresses with "-" and "_" are unaffected.
_UNSAFE_SEGMENT = re.compile(r"[/\\?#%\s\x00-\x1f\x7f]")


def path_segment(name: str, value: Any) -> str:
    """Return ``value`` unchanged if it is safe as one URL path segment, else raise.

    A value such as ``../../usage`` or ``x?limit=1000`` would otherwise send the
    request, and the client's API key, to a different path or query than the
    method was written for.
    """
    if (
        not isinstance(value, str)
        or value in ("", ".", "..")
        or _UNSAFE_SEGMENT.search(value)
    ):
        raise ValueError(f"{name} must be a single id or address, got {str(value)[:100]!r}")
    return value


def map_pool_sort_field(value: Optional[str]) -> str:
    """Map a (possibly legacy) pool sort field to the canonical search value.

    Canonical values pass through unchanged; known legacy values are translated;
    anything unknown falls back to the default ``volume_usd_24h``.
    """
    if value in POOL_SORT_CANONICAL:
        return value
    return POOL_SORT_FIELD_MAP.get(value, "volume_usd_24h")


def map_token_sort_field(value: Optional[str]) -> str:
    """Map a (possibly legacy) token sort field to the canonical search value.

    Canonical values pass through unchanged; known legacy values are translated;
    anything unknown falls back to the default ``volume_usd_24h``.
    """
    if value in TOKEN_SORT_CANONICAL:
        return value
    return TOKEN_SORT_FIELD_MAP.get(value, "volume_usd_24h")


def map_filter_params(filters: Dict[str, Any], name_map: Dict[str, str]) -> Dict[str, Any]:
    """Rename legacy filter param keys to their canonical search names.

    Keys absent from ``name_map`` are already canonical and pass through. Values
    are left untouched (None values are dropped later by ``_clean_params``).
    """
    return {name_map.get(key, key): value for key, value in filters.items()}


# ---------------------------------------------------------------------------
# Technical indicators, shared between PoolsAPI.get_indicator() and
# TokensAPI.get_indicator(). Both call the same query shape against
# /networks/{network}/pools/{address}/indicators and
# /networks/{network}/tokens/{address}/indicators.
# ---------------------------------------------------------------------------

VALID_INDICATOR_VALUES: Set[str] = {"rsi", "ema", "macd", "bbands", "vwap"}

# "1d" is accepted as an alias for "24h" on this endpoint only; it is kept
# separate from PoolsAPI.VALID_INTERVAL_VALUES / TokensAPI.VALID_INTERVAL_VALUES,
# which cover OHLCV and do not accept "1d".
VALID_INDICATOR_INTERVAL_VALUES: Set[str] = {
    "1m", "5m", "10m", "15m", "30m", "1h", "6h", "12h", "24h", "1d",
}

class CacheEntry:
    """Class representing a cached response with an expiration time."""

    def __init__(self, data: Any, expires_at: Optional[datetime] = None, endpoint: Optional[str] = None):
        """
        Initialize a new cache entry.

        Args:
            data: The data to cache
            expires_at: The time when the cache entry expires
            endpoint: The endpoint this entry was cached for, kept alongside the
                hashed cache key so clear_cache(prefix) can match against the
                real endpoint instead of its md5 digest.
        """
        self.data = data
        self.expires_at = expires_at
        self.endpoint = endpoint

    def is_expired(self) -> bool:
        """
        Check if the cache entry has expired.

        Returns:
            True if the cache entry has expired, False otherwise
        """
        return self.expires_at is not None and datetime.now() > self.expires_at


# Default cap on how many distinct (endpoint, params) responses a single API
# service keeps at once. Without a cap, a caller forwarding user-chosen search
# queries or ids builds one entry per distinct value for the life of the
# process. Picked generously above what a normal integration needs, small
# enough to bound memory under abuse.
DEFAULT_MAX_CACHE_ENTRIES = 256


class BaseAPI:
    """Base class for all API service classes."""

    def __init__(self, client: "DexPaprikaClient", max_cache_entries: int = DEFAULT_MAX_CACHE_ENTRIES):
        """
        Initialize a new API service.

        Args:
            client: The DexPaprika client instance
            max_cache_entries: Maximum number of distinct responses this service
                caches at once. Oldest unused entries are evicted first (LRU)
                once this limit is reached.
        """
        self.client = client
        self.max_cache_entries = max_cache_entries
        self._cache: "OrderedDict[str, CacheEntry]" = OrderedDict()  # TTL-based, size-bounded LRU cache

        # Default TTLs for different types of data
        self._cache_ttls = {
            "networks": timedelta(hours=24),  # Network and DEX lists rarely change
            "live": timedelta(minutes=1),     # Prices, OHLCV and transactions move constantly
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
        # Almost every path starts with /networks/, so match on what the path
        # ends in, most volatile first. Only the network and DEX lists
        # themselves get the long TTL.
        path = endpoint.split("?", 1)[0].rstrip("/")
        segments = path.split("/")
        if path.endswith(("/ohlcv", "/transactions", "/multi/prices", "/indicators")):
            return self._cache_ttls["live"]
        if path == "/networks" or segments[-1] == "dexes":
            return self._cache_ttls["networks"]
        if "pools" in segments:
            return self._cache_ttls["pools"]
        if "tokens" in segments:
            return self._cache_ttls["tokens"]
        if "stats" in segments:
            return self._cache_ttls["stats"]
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

        if cache_entry is not None:
            if not cache_entry.is_expired():
                # Mark as most-recently-used so a hot entry survives eviction.
                self._cache.move_to_end(cache_key)
                return cache_entry.data
            # Expired: drop it now rather than leaving it to occupy a slot
            # until something else reads or evicts it.
            del self._cache[cache_key]

        # Get fresh data
        result = self.client.get(endpoint, params=params)

        # Cache the result with appropriate TTL
        if ttl is None:
            ttl = self._get_ttl(endpoint)

        expires_at = datetime.now() + ttl
        self._store(cache_key, CacheEntry(result, expires_at, endpoint=endpoint))

        return result

    def _store(self, cache_key: str, entry: "CacheEntry") -> None:
        """Insert a cache entry, then enforce the size bound (LRU) and TTL.

        Expired entries are swept first so they never count against
        max_cache_entries between reads; what remains beyond the limit is
        trimmed from the least-recently-used end.
        """
        # Drop and re-insert so the key lands at the most-recently-used end.
        self._cache.pop(cache_key, None)
        self._cache[cache_key] = entry

        for key in [k for k, v in self._cache.items() if v.is_expired()]:
            del self._cache[key]

        while len(self._cache) > self.max_cache_entries:
            self._cache.popitem(last=False)  # evict least-recently-used

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
    
    def _validate_enum(self, param_name: str, value: Optional[str], valid_values: Set[str]) -> None:
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
    
    def _validate_range(self, param_name: str, value: Optional[Union[int, float]], min_val: Optional[Union[int, float]] = None, max_val: Optional[Union[int, float]] = None) -> None:
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
            # Match against the stored endpoint, not the cache key: the key is
            # an md5 digest of endpoint + params, so endpoint_prefix never
            # matched anything when compared against it directly.
            keys_to_remove = [
                key for key, cache_entry in self._cache.items()
                if cache_entry.endpoint is not None and endpoint_prefix in cache_entry.endpoint
            ]

            # Remove the entries
            for key in keys_to_remove:
                del self._cache[key]
        else:
            # Clear the entire cache
            self._cache.clear()
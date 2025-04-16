import requests
import time
import random
from typing import Optional, Dict, Any, Union, List
from requests.exceptions import RequestException, HTTPError, ConnectionError, Timeout

from .api.networks import NetworksAPI
from .api.pools import PoolsAPI
from .api.tokens import TokensAPI
from .api.search import SearchAPI
from .api.utils import UtilsAPI
from .api.dexes import DexesAPI


class DexPaprikaClient:
    # client for api

    def __init__(
        self,
        base_url: str = "https://api.dexpaprika.com",
        session: Optional[requests.Session] = None,
        user_agent: str = "DexPaprika-SDK-Python/0.1.0",
        max_retries: int = 4,
        backoff_times: List[float] = None,
    ):
        self.base_url = base_url.rstrip("/")
        self.session = session or requests.Session()
        self.user_agent = user_agent
        self.max_retries = max_retries
        self.backoff_times = backoff_times or [0.1, 0.5, 1.0, 5.0]  # 100ms, 500ms, 1s, 5s

        # services
        self.networks = NetworksAPI(self)
        self.pools = PoolsAPI(self)
        self.tokens = TokensAPI(self)
        self.search = SearchAPI(self)
        self.utils = UtilsAPI(self)
        self.dexes = DexesAPI(self)

    def _should_retry(self, exception: Exception) -> bool:
        """
        Determine if a request should be retried based on the exception.
        
        Args:
            exception: The exception that was raised
            
        Returns:
            True if the request should be retried, False otherwise
        """
        if isinstance(exception, (ConnectionError, Timeout)):
            # Always retry connection errors and timeouts
            return True
        elif isinstance(exception, HTTPError):
            # Retry server errors (5xx) but not client errors (4xx)
            return 500 <= exception.response.status_code < 600
        return False

    def request(
        self,
        method: str,
        endpoint: str,
        params: Optional[Dict[str, Any]] = None,
        data: Optional[Dict[str, Any]] = None,
        headers: Optional[Dict[str, str]] = None,
    ) -> Union[Dict[str, Any], list]:
        # make request to api
        url = f"{self.base_url}{endpoint}"
        
        # headers
        request_headers = {"User-Agent": self.user_agent}
        if headers: request_headers.update(headers)

        last_exception = None
        retries = 0
        
        while retries <= self.max_retries:
            try:
                # req
                response = self.session.request(
                    method=method, url=url, params=params, json=data, headers=request_headers,
                )

                # err check
                response.raise_for_status()

                # return data
                return response.json() if response.content else {}
                
            except Exception as e:
                last_exception = e
                retries += 1
                
                if retries > self.max_retries or not self._should_retry(e):
                    break
                
                # Get backoff time (use the last one if we've exhausted the list)
                backoff_index = min(retries - 1, len(self.backoff_times) - 1)
                backoff_time = self.backoff_times[backoff_index]
                
                # Add some jitter (±10% of the backoff time)
                jitter = random.uniform(-0.1 * backoff_time, 0.1 * backoff_time)
                sleep_time = backoff_time + jitter
                
                # Sleep before retrying
                time.sleep(max(0, sleep_time))
        
        # If we get here, all retries failed
        if last_exception:
            raise last_exception
        
        # This should never happen, but just in case
        raise Exception("Request failed but no exception was raised")
    
    def get(self, endpoint: str, params: Optional[Dict[str, Any]] = None) -> Union[Dict[str, Any], list]:
        # get req
        return self.request("GET", endpoint, params=params)
    
    def post(self, endpoint: str, data: Dict[str, Any], params: Optional[Dict[str, Any]] = None) -> Union[Dict[str, Any], list]:
        # post req
        return self.request("POST", endpoint, params=params, data=data)
        
    def clear_cache(self, endpoint_prefix: Optional[str] = None) -> None:
        """
        Clear the cache for all API services.
        
        Args:
            endpoint_prefix: Optional prefix to filter which cache entries to clear
        """
        for service in [self.networks, self.pools, self.tokens, self.search, self.utils, self.dexes]:
            service.clear_cache(endpoint_prefix) 
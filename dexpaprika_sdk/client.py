import os
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
from .exceptions import DeprecatedEndpointError


# Anything that would let a value break out of a header. A key carrying these
# is dropped rather than sanitised: a mangled key authenticates as nobody, and
# because the data endpoints ignore an unreadable key instead of rejecting it,
# the caller would never find out.
_HEADER_UNSAFE = ("\r", "\n", "\0")


def _resolve_api_key(explicit: Optional[str]) -> Optional[str]:
    """Explicit argument wins, then DEXPAPRIKA_API_KEY, then keyless."""
    raw = explicit if explicit is not None else os.environ.get("DEXPAPRIKA_API_KEY")
    if not isinstance(raw, str):
        return None
    key = raw.strip()
    if not key or any(c in key for c in _HEADER_UNSAFE):
        return None
    return key


def _package_version() -> str:
    # Deferred: __init__.py imports this module before it defines __version__,
    # so this can only be read once the package has finished importing. It is
    # called at construction time, never at import time.
    try:
        from . import __version__
        return __version__
    except Exception:  # pragma: no cover - defensive
        return "unknown"


class DexPaprikaClient:
    # client for api

    def __init__(
        self,
        base_url: str = "https://api.dexpaprika.com",
        session: Optional[requests.Session] = None,
        user_agent: Optional[str] = None,
        api_key: Optional[str] = None,
        max_retries: int = 4,
        backoff_times: List[float] = None,
    ):
        """
        Args:
            api_key: Optional. Falls back to the DEXPAPRIKA_API_KEY environment
                variable. Keyless is the default and keeps working: without a key
                the client behaves exactly as before.

                The key is sent as the **entire** Authorization value. There is no
                "Bearer" prefix and no other scheme word: the API checksums the raw
                header, so a scheme word returns 401. This is the most common reason
                a working key looks broken.

                The host does not change when a key is present. Free keys are served
                from the default base_url and only Pro moves to
                api-pro.dexpaprika.com, which callers set through base_url.
        """
        self.base_url = base_url.rstrip("/")
        self.session = session or requests.Session()
        # Was pinned to a literal that fell three minor versions behind the
        # package, so every request misreported which SDK sent it.
        self.user_agent = user_agent or f"DexPaprika-SDK-Python/{_package_version()}"
        self.api_key = _resolve_api_key(api_key)
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
        if isinstance(exception, DeprecatedEndpointError):
            # A deprecation hint is deterministic; retrying will never help.
            return False
        elif isinstance(exception, (ConnectionError, Timeout)):
            # Always retry connection errors and timeouts
            return True
        elif isinstance(exception, HTTPError):
            status = exception.response.status_code
            # 429 is the one 4xx worth retrying: it is transient by definition,
            # and the API says so in the body ("this is a per-minute limit, so
            # it clears on its own"). It also tells us how long to wait, both in
            # a Retry-After header and a retry_after field. Honour that in
            # _retry_delay rather than using the generic backoff, which is far
            # too short for a per-minute bucket.
            if status == 429:
                return True
            # Every other 4xx is deterministic; retrying only burns the quota.
            return 500 <= status < 600
        return False

    @staticmethod
    def _retry_after_seconds(exception: Exception) -> Optional[float]:
        """Seconds the server asked us to wait, or None if it did not say.

        Checked in header-then-body order because the header is cheap and always
        present on our 429s; the body field is the documented mirror of it and
        survives proxies that strip headers.
        """
        response = getattr(exception, "response", None)
        if response is None:
            return None
        raw = response.headers.get("Retry-After")
        if raw is None:
            try:
                raw = (response.json() or {}).get("retry_after")
            except ValueError:
                raw = None
        if raw is None:
            return None
        try:
            seconds = float(raw)
        except (TypeError, ValueError):
            # Retry-After may be an HTTP date. We do not parse it; the caller
            # falls back to the normal backoff rather than guessing.
            return None
        # Clamp: a hostile or buggy value must not park a caller for an hour.
        return max(0.0, min(seconds, 60.0))

    def _deprecation_error(self, response) -> Optional[DeprecatedEndpointError]:
        """Build a DeprecatedEndpointError if the error body carries a replacement.

        The API self-documents removed endpoints by returning a non-2xx response
        whose JSON body includes a "replacement" field. This keys on the presence
        of that field for ANY error status, so future deprecations surface the
        same way without hardcoding endpoints or status codes.

        Defensive by design: the body may not be JSON, may not be an object, or
        may lack "replacement". In any of those cases this returns None so the
        caller falls back to the current ``raise_for_status`` behavior.

        Args:
            response: The ``requests.Response`` for a non-2xx request.

        Returns:
            A DeprecatedEndpointError when a replacement hint is present, else None.
        """
        try:
            body = response.json()
        except Exception:
            # Not JSON (or unreadable body): fall back to default handling.
            return None

        if not isinstance(body, dict):
            return None

        replacement = body.get("replacement")
        if not replacement:
            return None

        message = body.get("message") or "endpoint removed"
        return DeprecatedEndpointError(
            message=message,
            replacement=replacement,
            status_code=getattr(response, "status_code", None),
            response=response,
        )

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
        if self.api_key:
            # The whole value, with no scheme word in front of it.
            request_headers["Authorization"] = self.api_key
        if headers: request_headers.update(headers)

        last_exception = None
        retries = 0
        
        while retries <= self.max_retries:
            try:
                # req
                response = self.session.request(
                    method=method, url=url, params=params, json=data, headers=request_headers,
                )

                # err check: surface the API's deprecation hint (a "replacement"
                # field on an error body) as a typed error before the generic
                # HTTPError. Guarded on a real error status so mocked responses
                # and success responses are untouched.
                status_code = getattr(response, "status_code", None)
                if isinstance(status_code, int) and status_code >= 400:
                    deprecation = self._deprecation_error(response)
                    if deprecation is not None:
                        raise deprecation
                response.raise_for_status()

                # return data
                return response.json() if response.content else {}
                
            except Exception as e:
                last_exception = e
                retries += 1
                
                if retries > self.max_retries or not self._should_retry(e):
                    break
                
                # A server-supplied Retry-After wins. Our own backoff tops out
                # at 5s, which is useless against a per-minute rate limit.
                asked = self._retry_after_seconds(e)
                if asked is not None:
                    backoff_time = asked
                else:
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
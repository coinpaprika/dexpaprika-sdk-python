import requests
from typing import Optional, Dict, Any, Union

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
    ):
        self.base_url = base_url.rstrip("/")
        self.session = session or requests.Session()
        self.user_agent = user_agent

        # services
        self.networks = NetworksAPI(self)
        self.pools = PoolsAPI(self)
        self.tokens = TokensAPI(self)
        self.search = SearchAPI(self)
        self.utils = UtilsAPI(self)
        self.dexes = DexesAPI(self)

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

        # req
        response = self.session.request(
            method=method, url=url, params=params, json=data, headers=request_headers,
        )

        # err check
        response.raise_for_status()

        # return data
        return response.json() if response.content else {}
    
    def get(self, endpoint: str, params: Optional[Dict[str, Any]] = None) -> Union[Dict[str, Any], list]:
        # get req
        return self.request("GET", endpoint, params=params)
    
    def post(self, endpoint: str, data: Dict[str, Any], params: Optional[Dict[str, Any]] = None) -> Union[Dict[str, Any], list]:
        # post req
        return self.request("POST", endpoint, params=params, data=data) 
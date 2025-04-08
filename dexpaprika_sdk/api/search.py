from urllib.parse import quote

from .base import BaseAPI
from ..models.search import SearchResult


class SearchAPI(BaseAPI):
    """API service for search-related endpoints."""
    
    def search(self, query: str) -> SearchResult:
        """
        Search for tokens, pools, and DEXes by name or identifier.
        
        Args:
            query: Search term (e.g., "uniswap", "bitcoin", or a token address)
            
        Returns:
            Search results across tokens, pools, and DEXes
        """
        params = {"query": query}
        data = self._get("/search", params=params)
        return SearchResult(**data) 
from .base import BaseAPI
from ..models.utils import Stats


class UtilsAPI(BaseAPI):
    """API service for utility endpoints."""
    
    def get_stats(self) -> Stats:
        """
        Get high-level statistics about the DexPaprika ecosystem.
        
        Returns:
            Statistics about the DexPaprika ecosystem
        """
        data = self._get("/stats")
        return Stats(**data) 
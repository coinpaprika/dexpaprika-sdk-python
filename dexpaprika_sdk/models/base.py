from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any, Generic, TypeVar

T = TypeVar('T')

class PageInfo(BaseModel):
    """Page information for paginated results."""
    
    limit: int = Field(..., description="Number of items per page")
    page: int = Field(..., description="Current page number")
    total_items: Optional[int] = Field(None, description="Total number of items")
    total_pages: Optional[int] = Field(None, description="Total number of pages")
    next_cursor: Optional[str] = Field(None, description="Next cursor for cursor-based pagination")

class PaginatedResponse(BaseModel, Generic[T]):
    """Generic paginated response."""
    
    page_info: PageInfo = Field(..., description="Pagination information") 
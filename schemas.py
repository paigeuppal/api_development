from pydantic import BaseModel
from typing import Optional

# pydantic model for the API response - ensures consistent output format and validation
class MovieAdjustedResponse(BaseModel):
    movie_id: int
    title: str
    release_year: int
    original_budget: float
    original_revenue: float
    adjusted_budget: float 
    adjusted_revenue: float 
    roi_percentage: float 

# Schema for inputting data (POST/PUT)
class MovieCreateUpdate(BaseModel):
    title: str
    release_year: int
    budget: float
    revenue: float

# Schema for PARTIAL updates (PATCH)
class MovieUpdate(BaseModel):
    title: Optional[str] = None
    release_year: Optional[int] = None
    budget: Optional[float] = None
    revenue: Optional[float] = None
from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime

# Get the current year so validation automatically updates every year
current_year = datetime.now().year

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
    # movie title must be between 1 and 250 characters
    title: str = Field(..., min_length=1, max_length=250)
    
    # release year must be between 1888 and the current year + 1
    release_year: int = Field(..., ge=1888, le=current_year + 1)
    
    # finances must be >=to 0
    budget: float = Field(..., ge=0)
    revenue: float = Field(..., ge=0)

# Schema for partial updates (PATCH)
class MovieUpdate(BaseModel):
    title: Optional[str] = Field(None, min_length=1, max_length=250)
    release_year: Optional[int] = Field(None, ge=1888, le=current_year + 1)
    budget: Optional[float] = Field(None, ge=0)
    revenue: Optional[float] = Field(None, ge=0)
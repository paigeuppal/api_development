from fastapi import FastAPI, HTTPException, Depends
from fastapi_mcp import FastApiMCP
from pydantic import BaseModel
#from sqlalchemy import create_engine, Column, Integer, String, Float
#from sqlalchemy.orm import declarative_base, sessionmaker, Session
from typing import Optional

#from fastapi import FastAPI, HTTPException, Depends
#from fastapi_mcp import FastApiMCP
from sqlalchemy.orm import Session

from database import get_db, Base, Movie, InflationRate

# # Connects to blockbuster.db 
# SQLALCHEMY_DATABASE_URL = "sqlite:///blockbuster.db"
# engine = create_engine(SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False})
# SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
# Base = declarative_base()

# # Redefine models so FastAPI knows how to read the tables
# class Movie(Base):
#     __tablename__ = 'movies'
#     id = Column(Integer, primary_key=True, index=True)
#     title = Column(String, nullable=False)
#     release_year = Column(Integer, nullable=False)
#     budget = Column(Float, nullable=False)
#     revenue = Column(Float, nullable=False)

# class InflationRate(Base):
#     __tablename__ = 'inflation_rates'
#     year = Column(Integer, primary_key=True)
#     cpi = Column(Float, nullable=False)

# # Dependency to safely open and close a database connection for each user request
# def get_db():
#     db = SessionLocal()
#     try:
#         yield db
#     finally:
#         db.close()

# pydantic model for the API response - ensures consistent output format and validation
class MovieAdjustedResponse(BaseModel):
    movie_id: int
    title: str
    release_year: int
    original_budget: float
    original_revenue: float
    adjusted_budget: float # inflation adjusted budget
    adjusted_revenue: float # inflation adjusted revenue
    roi_percentage: float # Return on Investment percentage based on adjusted values

# FastAPI app instance
app = FastAPI(
    title="Adjusted Blockbuster API",
    description="An API that calculates what the box office revenue of a movie would be in today's ecconomy"
)

@app.get("/")
def read_root():
    return {"message": "Welcome to the Adjusted Blockbuster API! Go to /docs to see the documentation."}

# READ Endpoint to return the adjusted budget, revenue, and ROI for a given movie ID
@app.get("/movies/adjusted/{movie_id}", response_model=MovieAdjustedResponse)
def get_adjusted_movie(movie_id: int, db: Session = Depends(get_db)):
    
    # search for movie by ID in database, if not found return 404 error
    movie = db.query(Movie).filter(Movie.id == movie_id).first()
    if not movie:
        raise HTTPException(status_code=404, detail="Movie not found in the database")

    # search for historical inflation rate (CPI) for the year the movie came out
    historical_cpi = db.query(InflationRate).filter(InflationRate.year == movie.release_year).first()
    
    # search for the most recent inflation rate in database 
    modern_cpi = db.query(InflationRate).order_by(InflationRate.year.desc()).first()

    # check for inflation data, don't calculate if missing 
    if not historical_cpi or not modern_cpi:
        raise HTTPException(status_code=400, detail="Inflation data is missing for this calculation")

    # Adjustment calculation: 
    # today's cost = original cost * (CPI today / CPI in year of release)
    economic_adjustment = modern_cpi.cpi / historical_cpi.cpi
    adj_budget = movie.budget * economic_adjustment
    adj_revenue = movie.revenue * economic_adjustment
    
    # calculate ROI %: ((Revenue - Budget) / Budget) * 100
    roi = ((adj_revenue - adj_budget) / adj_budget) * 100 if adj_budget > 0 else 0

    # Package response into schema previously defined & return as JSON
    return {
        "movie_id": movie.id,
        "title": movie.title,
        "release_year": movie.release_year,
        "original_budget": movie.budget,
        "original_revenue": movie.revenue,
        "adjusted_budget": round(adj_budget, 2),
        "adjusted_revenue": round(adj_revenue, 2),
        "roi_percentage": round(roi, 2)
    }
    
# SEARCH endpoint - find movies by a partial title match as not guaranteed to know movieID
@app.get("/movies/search/")
def search_movies(title: str, db: Session = Depends(get_db)):
    
    # case-insensitive search for movies with titles that contain the search term, returns a list of matches
    movies = db.query(Movie).filter(Movie.title.ilike(f"%{title}%")).all()
    
    if not movies:
        raise HTTPException(status_code=404, detail=f"No movies found matching '{title}'.")
        
    # create a simplified list of results to output to user
    results = []
    for m in movies:
        results.append({
            "movie_id": m.id,
            "title": m.title,
            "release_year": m.release_year
        })
        
    return {"matches_found": len(results), "results": results}
    
# Schema for inputting data
class MovieCreateUpdate(BaseModel):
    title: str
    release_year: int
    budget: float
    revenue: float

# CREATE endpoint - ability to add a new film to the database, with duplication validation 
@app.post("/movies/")
def create_movie(movie: MovieCreateUpdate, db: Session = Depends(get_db)):
    
    # checking for film with the same title (case-insensitive) and release year to prevent duplicates
    existing_movie = db.query(Movie).filter(
        Movie.title.ilike(movie.title), 
        Movie.release_year == movie.release_year
    ).first() 

    if existing_movie:
        # If movie exists in database, throw 400 Bad Request error
        raise HTTPException(
            status_code=400, 
            detail=f"Error: '{movie.title}' ({movie.release_year}) already exists in the database with ID {existing_movie.id}."
        )

    # if film not in database, create the new movie record and add to database
    new_movie = Movie(
        title=movie.title,
        release_year=movie.release_year,
        budget=movie.budget,
        revenue=movie.revenue
    )
    db.add(new_movie)
    db.commit()
    db.refresh(new_movie)
    return {"message": f"Added '{new_movie.title}' to the database successfully.", "movie_id": new_movie.id}

# UPDATE endpoint - Amend existing movie data by ID, overwrites all of the fields 
@app.put("/movies/{movie_id}")
def update_movie(movie_id: int, updated_movie: MovieCreateUpdate, db: Session = Depends(get_db)):
    db_movie = db.query(Movie).filter(Movie.id == movie_id).first()
    
    # check if movie exists in database, if not return 404 error
    if not db_movie:
        raise HTTPException(status_code=404, detail="Movie not found")
        
    # update and overwrite the old data with the new data
    db_movie.title = updated_movie.title
    db_movie.release_year = updated_movie.release_year
    db_movie.budget = updated_movie.budget
    db_movie.revenue = updated_movie.revenue
    
    db.commit()
    db.refresh(db_movie)
    return {"message": f"Successfully updated movie ID {movie_id}", "title": db_movie.title}

# Schema for PARTIAL updates (PATCH)
class MovieUpdate(BaseModel):
    title: Optional[str] = None
    release_year: Optional[int] = None
    budget: Optional[float] = None
    revenue: Optional[float] = None
    
# PATCH - Partially updating fields - update fields without overwriting entire record 
@app.patch("/movies/{movie_id}")
def update_movie_detail(movie_id: int, updated_data: MovieUpdate, db: Session = Depends(get_db)):
    
    # check if movie exists in database, if not return 404 error
    db_movie = db.query(Movie).filter(Movie.id == movie_id).first()
    if not db_movie:
        raise HTTPException(status_code=404, detail=f"Movie with ID {movie_id} not found.")
        
    old_title = db_movie.title # saved for the success message 
    
    # exclude_unset=True to ignore any fields that were not included in the PATCH request
    # so only update the fields that were actually sent by the user
    update_data_dict = updated_data.model_dump(exclude_unset=True)
    
    # loop through and update only those specific fields
    for key, value in update_data_dict.items():
        setattr(db_movie, key, value)
    
    db.commit()
    db.refresh(db_movie)
    
    # Return the fully updated movie so the user knows exactly what they just changed
    return {
        "message": f"Successfully updated '{old_title}'!",
        "current_movie_state": {
            "id": db_movie.id,
            "title": db_movie.title,
            "release_year": db_movie.release_year,
            "budget": db_movie.budget,
            "revenue": db_movie.revenue
        }
    }

# Analytics endpoint - calculates the top n most profitable movies adjusted for inflation
@app.get("/analytics/leaderboard")
def get_profitability_leaderboard(top: int = 10, db: Session = Depends(get_db)):
    
    # fetch all movies and all inflation rates at once
    movies = db.query(Movie).all()
    rates = db.query(InflationRate).all()
    
    if not movies or not rates:
        raise HTTPException(status_code=400, detail="Not enough data to calculate a leaderboard.")
    
    # create a dictionary to look up CPI 
    cpi_map = {rate.year: rate.cpi for rate in rates}
    
    # find most recent CPI to use as today's inflation rate for adjustment calculations
    modern_cpi = max(rates, key=lambda x: x.year).cpi
    
    leaderboard = []
    
    # loop through each movie, calculate the adjusted budget, revenue, and ROI, and add to the leaderboard list
    for movie in movies:
        historical_cpi = cpi_map.get(movie.release_year)
        
        # Skip movies if we don't have inflation data for their specific release year
        if not historical_cpi:
            continue 
            
        multiplier = modern_cpi / historical_cpi
        adj_budget = movie.budget * multiplier
        adj_revenue = movie.revenue * multiplier
        
        roi = ((adj_revenue - adj_budget) / adj_budget) * 100 if adj_budget > 0 else 0
        
        leaderboard.append({
            "movie_id": movie.id,
            "title": movie.title,
            "release_year": movie.release_year,
            "roi_percentage": round(roi, 2)
        })
        
    # sort the leaderboard by ROI in descending order so the most profitable movies are at the top
    leaderboard.sort(key=lambda x: x["roi_percentage"], reverse=True)
    
    # return top n movies, where n is determined by user 
    return {"leaderboard_size": top, "top_movies": leaderboard[:top]}

# DELETE endpoint - Remove a movie from the database
@app.delete("/movies/{movie_id}")
def delete_movie(movie_id: int, db: Session = Depends(get_db)):
    db_movie = db.query(Movie).filter(Movie.id == movie_id).first()
    
    if not db_movie:
        raise HTTPException(status_code=404, detail=f"Movie with ID {movie_id} not found.")
        
    db.delete(db_movie)
    db.commit()
    return {"message": f"Successfully deleted '{db_movie.title}' from the database."}

# create and mount the MCP server directly to FastAPI app
mcp = FastApiMCP(app)
mcp.mount_sse()
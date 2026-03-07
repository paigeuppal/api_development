from fastapi import FastAPI, HTTPException, Depends
from pydantic import BaseModel
from sqlalchemy import create_engine, Column, Integer, String, Float
from sqlalchemy.orm import declarative_base, sessionmaker, Session


# Connects to blockbuster.db 
SQLALCHEMY_DATABASE_URL = "sqlite:///blockbuster.db"
engine = create_engine(SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

# Redefine models so FastAPI knows how to read the tables
class Movie(Base):
    __tablename__ = 'movies'
    id = Column(Integer, primary_key=True, index=True)
    title = Column(String, nullable=False)
    release_year = Column(Integer, nullable=False)
    budget = Column(Float, nullable=False)
    revenue = Column(Float, nullable=False)

class InflationRate(Base):
    __tablename__ = 'inflation_rates'
    year = Column(Integer, primary_key=True)
    cpi = Column(Float, nullable=False)

# Dependency to safely open and close a database connection for each user request
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

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
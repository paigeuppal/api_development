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
from sqlalchemy import create_engine, Column, Integer, String, Float
from sqlalchemy.orm import declarative_base, sessionmaker


# Connects to blockbuster.db 
SQLALCHEMY_DATABASE_URL = "sqlite:///blockbuster.db"
engine = create_engine(SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

# Dependency to safely open and close a database connection for each user request
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

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
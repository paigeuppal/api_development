import pandas as pd
from sqlalchemy import create_engine, Column, Integer, String, Float
from sqlalchemy.orm import declarative_base, sessionmaker

# Reading and cleaning data from the CSV files
print("Reading CSV files")

# Load movie dataset 
movies_df = pd.read_csv('data/tmdb_5000_movies.csv')
# Drop movies that have 0 budget or 0 revenue (bad data)
movies_df = movies_df[(movies_df['budget'] > 0) & (movies_df['revenue'] > 0)].copy()
# Extract just the year from the 'release_date'
movies_df['release_year'] = pd.to_datetime(movies_df['release_date'], errors='coerce').dt.year
movies_df = movies_df.dropna(subset=['release_year']) 
movies_df['release_year'] = movies_df['release_year'].astype(int)

# Load US inflation data
inflation_df = pd.read_csv('data/US_inflation_rates.csv')
# Extract year from the date
inflation_df['year'] = pd.to_datetime(inflation_df['date']).dt.year
# Calculate the average Consumer Price Index (CPI) for each year as inflation is recorded monthly in dataset
yearly_cpi = inflation_df.groupby('year')['value'].mean().reset_index()

# Set up database schema 
Base = declarative_base()

class Movie(Base):
    __tablename__ = 'movies'
    id = Column(Integer, primary_key=True)
    title = Column(String, nullable=False)
    release_year = Column(Integer, nullable=False)
    budget = Column(Float, nullable=False)
    revenue = Column(Float, nullable=False)
    genres = Column(String, nullable=True)

class InflationRate(Base):
    __tablename__ = 'inflation_rates'
    year = Column(Integer, primary_key=True)
    cpi = Column(Float, nullable=False)

# Create SQLite database and tables
print("Building SQLite database...")
engine = create_engine('sqlite:///blockbuster.db')
Base.metadata.create_all(engine)

Session = sessionmaker(bind=engine)
session = Session()

# Insert Movies
print("Inserting movies...")
for _, row in movies_df.iterrows():
    movie = Movie(
        title=row['original_title'],
        release_year=row['release_year'],
        budget=row['budget'],
        revenue=row['revenue'],
        genres=str(row['genres'])
    )
    session.add(movie)

# Insert CPI Data
print("Inserting inflation data...")
for _, row in yearly_cpi.iterrows():
    rate = InflationRate(
        year=int(row['year']),
        cpi=row['value']
    )
    session.add(rate)

session.commit()
session.close()

print("blockbuster.db has been created and populated.")
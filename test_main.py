from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

# import app and database components from main.py file
from main import app, get_db, Base, Movie, InflationRate

# use sqlite:///:memory: to create a database just for testing locally 
SQLALCHEMY_DATABASE_URL = "sqlite:///:memory:"

# add poolclass=StaticPool to stop the RAM database from evaporating between tests
engine = create_engine(
    SQLALCHEMY_DATABASE_URL, 
    connect_args={"check_same_thread": False},
    poolclass=StaticPool
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# create blank tables (movies, inflation_rates) in the database 
Base.metadata.create_all(bind=engine)

# override blockbuster.db with the in-memory database for testing purposes
def override_get_db():
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()

app.dependency_overrides[get_db] = override_get_db

# create a TestClient instance to use to simulate requests to API
client = TestClient(app)

## TESTS BEGIN HERE ## 

# Test 1: Root endpoint returns expected welcome message
def test_read_root():
    # Test client visits root endpoint
    response = client.get("/")
    
    # prove the server didn't crash (200 OK)
    assert response.status_code == 200 
    
    # prove the API returned the exact right message
    assert response.json() == {"message": "Welcome to the Adjusted Blockbuster API! Go to /docs to see the documentation."}
    
# Test 2: CREATE happy path - user adds a new movie successfully
def test_create_movie():
    # Test client sends a POST request to the /movies/ endpoint with a new movie's data in JSON format
    response = client.post(
        "/movies/",
        json={
            "title": "Create Movie Test",
            "release_year": 2024,
            "budget": 500000,
            "revenue": 2000000
        }
    )
    
    # prove the API accepted it (200 OK)
    assert response.status_code == 200
    
    # prove the API sent back the correct success message
    data = response.json()
    assert data["message"] == "Added 'Create Movie Test' to the database successfully."
    
    # prove the database actually generated a unique ID for our new movie
    assert "movie_id" in data


# Test 3: CREATE sad path - user tries to add a duplicate movie and gets an error
def test_create_duplicate_movie():
    
    # Test that duplicate movies are blocked, movie with same title and release year 
    # already exists in the database from previous test
    response = client.post(
        "/movies/",
        json={
            "title": "Create Movie Test",
            "release_year": 2024,
            "budget": 100,
            "revenue": 500
        }
    )
    
    # prove the API blocked it (400 Bad Request)
    assert response.status_code == 400
    
    # prove the API sent error message back
    assert "already exists in the database" in response.json()["detail"]
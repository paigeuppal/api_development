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
            "title": "Movie Test",
            "release_year": 2024,
            "budget": 500000,
            "revenue": 2000000
        }
    )
    
    # prove the API accepted it (200 OK)
    assert response.status_code == 200
    
    # prove the API sent back the correct success message
    data = response.json()
    assert data["message"] == "Added 'Movie Test' to the database successfully."
    
    # prove the database actually generated a unique ID for our new movie
    assert "movie_id" in data


# Test 3: CREATE erroneous path - user tries to add a duplicate movie and gets an error
def test_create_duplicate_movie():
    
    # Test that duplicate movies are blocked, movie with same title and release year 
    # already exists in the database from previous test
    response = client.post(
        "/movies/",
        json={
            "title": "Movie Test",
            "release_year": 2024,
            "budget": 100,
            "revenue": 500
        }
    )
    
    # prove the API blocked it (400 Bad Request)
    assert response.status_code == 400
    
    # prove the API sent error message back
    assert "already exists in the database" in response.json()["detail"]
    
# Test 4: SEARCH happy path - user searches for a movie by partial title and finds it successfully
def test_search_movie():
    # Search for a partial string 
    response = client.get("/movies/search/?title=test")
    
    assert response.status_code == 200
    data = response.json()
    
    # Prove it found at least 1 match
    assert data["matches_found"] >= 1
    # Prove the title of the found movie matches the one created earlier 
    assert data["results"][0]["title"] == "Movie Test"


# Test 5: UPDATE Patch happy path - user updates just the revenue of a movie, leaving the budget completely untouched
def test_update_movie():
    # Only update the revenue, leaving the budget completely untouched
    response = client.patch(
        "/movies/1", #ID 1 because it's the first movie created in Test 2
        json={"revenue": 9999999}
    )
    
    assert response.status_code == 200
    data = response.json()
    
    # Prove the success message is correct
    assert "Successfully updated" in data["message"]
    # Prove the revenue changed
    assert data["current_movie_state"]["revenue"] == 9999999
    # Prove the budget stayed exactly the same as when we created it!
    assert data["current_movie_state"]["budget"] == 500000


# Test 6: DELETE happy path - user deletes a movie successfully
def test_delete_movie():
    # Delete the movie
    response = client.delete("/movies/1")
    
    assert response.status_code == 200
    assert "Successfully deleted" in response.json()["message"]
    
    # Prove it's actually gone by trying to search for it again
    verify_response = client.get("/movies/search/?title=test")
    assert verify_response.status_code == 404
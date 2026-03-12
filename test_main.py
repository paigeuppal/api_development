import os
# Inject a fake test key into the environment BEFORE the app imports security.py
os.environ["API_KEY"] = "YouShallNotPass"

from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

# import app and database components from main.py and database.py files
from main import app
from database import get_db, Base, Movie, InflationRate

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
        headers={"X-API-Key": "YouShallNotPass"}, # include the testing API key in the header to pass authentication
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
        headers={"X-API-Key": "YouShallNotPass"},
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
    
    # Prove it found at least 1 match using the new key name
    assert data["matches_returned"] >= 1
    
    # Prove the pagination defaults are working (skip=0, limit=10)
    assert data["skip"] == 0
    assert data["limit"] == 10
    
    # Prove the title of the found movie matches the one created earlier 
    assert data["results"][0]["title"] == "Movie Test"


# Test 5: UPDATE Patch happy path - user updates just the revenue of a movie, leaving the budget completely untouched
def test_update_movie():
    # Only update the revenue, leaving the budget completely untouched
    response = client.patch(
        "/movies/1", #ID 1 because it's the first movie created in Test 2
        headers={"X-API-Key": "YouShallNotPass"},
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
    response = client.delete("/movies/1", headers={"X-API-Key": "YouShallNotPass"})
    
    assert response.status_code == 200
    assert "Successfully deleted" in response.json()["message"]
    
    # Prove it's actually gone by trying to search for it again
    verify_response = client.get("/movies/search/?title=test")
    assert verify_response.status_code == 404
    
# Test 7: Reject movies that have a release year in the future - validation test
def test_create_movie_future_year():
    response = client.post(
        "/movies/",
        headers={"X-API-Key": "YouShallNotPass"},
        json={
            "title": "Time Traveler's Dilemma",
            "release_year": 3050, # invalid future year
            "budget": 100000,
            "revenue": 500000
        }
    )
    # Prove Pydantic blocked it automatically
    assert response.status_code == 422 
    # Prove the error message specifically mentions the release_year field
    assert response.json()["detail"][0]["loc"][-1] == "release_year"


# Test 8: Reject movies that have a negative budget - validation test
def test_create_movie_negative_budget():
    response = client.post(
        "/movies/",
        headers={"X-API-Key": "YouShallNotPass"},
        json={
            "title": "The Debt",
            "release_year": 2010,
            "budget": -50000, # invalid negative budget
            "revenue": 1000000
        }
    )
    assert response.status_code == 422
    assert response.json()["detail"][0]["loc"][-1] == "budget"


# Test 9: reject movies that have an empty title - validation test
def test_create_movie_empty_title():
    response = client.post(
        "/movies/",
        headers={"X-API-Key": "YouShallNotPass"},
        json={
            "title": "", # invalid empty title
            "release_year": 2020,
            "budget": 5000,
            "revenue": 10000
        }
    )
    assert response.status_code == 422
    assert response.json()["detail"][0]["loc"][-1] == "title"
    
# Test 10: reject missing API key - authentication test
def test_missing_api_key():
    # Send a request with NO header at all
    response = client.delete("/movies/1")
    
    assert response.status_code == 401
    # expect FastAPI's default "Missing Header" message here
    assert response.json()["detail"] == "Not authenticated"


# Test 11: reject incorrect API key - authentication test
def test_wrong_api_key():
    # Send a request with a completely incorrect API key
    response = client.delete(
        "/movies/1",
        headers={"X-API-Key": "HoustonWeHaveAProblem"}
    )
    
    assert response.status_code == 401
    # expect custom error message
    assert response.json()["detail"] == "Unauthorised: Invalid API Key"
    
# Test 12: check JSON string is formatted correctly
def test_movie_genre_json_parsing():
    # Inject fake inflation data directly into the database for this test 
    db = TestingSessionLocal()
    db.add(InflationRate(year=2024, cpi=311.0))
    db.commit()
    db.close()
    
    # Create a new movie with a busy JSON string in the genre field
    create_res = client.post(
        "/movies/",
        headers={"X-API-Key": "YouShallNotPass"},
        json={
            "title": "Genre Parsing Test",
            "release_year": 2024,
            "budget": 1000,
            "revenue": 5000,
            "genres": '[{"id": 28, "name": "Action"}, {"id": 12, "name": "Adventure"}]'
        }
    )
    movie_id = create_res.json()["movie_id"]
    
    # Fetch the movie back via the adjusted endpoint 
    response = client.get(f"/movies/adjusted/{movie_id}")
    assert response.status_code == 200
    data = response.json()
    
    # Prove the genres field was cleaned up correctly in the response
    assert data["genres"] == "Action, Adventure"


# Test 13: Success predictor happy path 
def test_success_predictor_valid():
    # add another Action movie so we have multiple historical comps to analyse
    client.post(
        "/movies/",
        headers={"X-API-Key": "YouShallNotPass"},
        json={
            "title": "Failed Action Blockbuster",
            "release_year": 2024,
            "budget": 1100, # Very close to the 1000 budget from Test 12
            "revenue": 500, # Lost money
            "genres": '[{"id": 28, "name": "Action"}]'
        }
    )
    
    # run the predictor looking for an Action movie with a $1000 budget.
    # both created movies should be in the cohort 
    response = client.get("/analytics/success-predictor/?proposed_budget=1000&genre=Action")
    
    assert response.status_code == 200
    data = response.json()
    
    # prove the payload structure is formatted correctly 
    assert "predictor_parameters" in data
    assert "risk_assessment" in data
    assert "genre_insights" in data
    
    # prove the cohort statistics are correct 
    assert data["risk_assessment"]["cohort_size"] == 2
    assert data["risk_assessment"]["success_rate_percentage"] == 50.0
    assert data["risk_assessment"]["rating"] == "Caution"


# Test 14: Predictor handles empty data safely
def test_success_predictor_no_data():
    # Query a genre and budget combination that definitely doesn't exist in mock DB
    response = client.get("/analytics/success-predictor/?proposed_budget=50000000&genre=Musical")
    
    assert response.status_code == 200
    assert "error" in response.json()
    assert "Not enough historical data" in response.json()["error"]
    
# Test 15: CREATE Inflation happy path - admin adds new CPI data successfully
def test_create_inflation_success():
    response = client.post(
        "/analytics/inflation/",
        headers={"X-API-Key": "YouShallNotPass"},
        json={
            "year": 2025,
            "cpi": 320.5
        }
    )
    
    assert response.status_code == 200
    assert response.json()["message"] == "Added new inflation data for 2025"


# Test 16: CREATE Inflation erroneous path - admin tries to add a year that already exists
def test_create_inflation_duplicate():
    # 1. Create the initial record for 2026
    client.post(
        "/analytics/inflation/",
        headers={"X-API-Key": "YouShallNotPass"},
        json={"year": 2026, "cpi": 325.0}
    )
    
    # 2. Attempt to create the exact same year again with a different CPI
    response = client.post(
        "/analytics/inflation/",
        headers={"X-API-Key": "YouShallNotPass"},
        json={"year": 2026, "cpi": 330.0}
    )
    
    # Prove the API blocked the duplicate creation
    assert response.status_code == 400
    assert "already exists" in response.json()["detail"]


# Test 17: UPDATE Inflation happy path - admin updates existing CPI data successfully
def test_update_inflation_success():
    # 1. First, ensure the year 2027 exists
    client.post(
        "/analytics/inflation/",
        headers={"X-API-Key": "YouShallNotPass"},
        json={"year": 2027, "cpi": 330.0}
    )
    
    # 2. Now, update it using the PUT endpoint
    # Note: CPI is passed as a query parameter based on your FastAPI route setup
    response = client.put(
        "/analytics/inflation/2027?cpi=335.5",
        headers={"X-API-Key": "YouShallNotPass"}
    )
    
    assert response.status_code == 200
    assert response.json()["message"] == "Updated CPI for 2027 to 335.5"


# Test 18: UPDATE Inflation erroneous path - admin tries to update a year that doesn't exist
def test_update_inflation_not_found():
    # Try to update a year we haven't created in the test database (like 2050)
    response = client.put(
        "/analytics/inflation/2050?cpi=400.0",
        headers={"X-API-Key": "YouShallNotPass"}
    )
    
    # Prove the API correctly returns a Not Found error
    assert response.status_code == 404
    assert "not found" in response.json()["detail"]
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

# import app and database components from main.py file
from main import app, get_db, Base, Movie, InflationRate


# use sqlite:///:memory: to create a database just for testing locally 
SQLALCHEMY_DATABASE_URL = "sqlite:///:memory:"
engine = create_engine(SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False})
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
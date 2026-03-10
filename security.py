import os
from fastapi import HTTPException, Depends
from fastapi.security import APIKeyHeader
from dotenv import load_dotenv

# open the .env vault and load the variable into memory
load_dotenv()

# read the key from the environment
SECRET_KEY = os.getenv("API_KEY")

# Look for a header called "X-API-Key" in every incoming request
api_key_header = APIKeyHeader(name="X-API-Key")

def verify_api_key(api_key: str = Depends(api_key_header)):
    """
    This dependency checks if the user provided the correct key.
    If they didn't, it immediately throws a 401 Unauthorised error.
    """
    if api_key != SECRET_KEY:
        raise HTTPException(status_code=401, detail="Unauthorised: Invalid API Key")
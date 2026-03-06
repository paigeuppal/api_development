from fastapi import FastAPI

app = FastAPI(
    title="Adjusted Blockbuster API",
    description="An API that calculates what the box office revenue of a movie would be in today's ecconomy"
)

@app.get("/")
def read_root():
    return {"message": "Welcome to the Adjusted Blockbuster API! Go to /docs to see the documentation."}
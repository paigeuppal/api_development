from fastapi import FastAPI, HTTPException, Depends
from fastapi_mcp import FastApiMCP
from sqlalchemy.orm import Session
from fastapi.middleware.cors import CORSMiddleware
import json

from database import get_db, Base, Movie, InflationRate
from schemas import MovieAdjustedResponse, MovieCreateUpdate, MovieUpdate
from security import verify_api_key

# FastAPI app instance
app = FastAPI(
    title="Adjusted Blockbuster API",
    description="An API that calculates what the box office revenue of a movie would be in today's ecconomy"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], # Allows any frontend to access the API 
    allow_credentials=True,
    allow_methods=["*"], # Allows all HTTP methods
    allow_headers=["*"], # Allows all headers 
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
    
    # search for the most recent , tags = ["Analytics"]inflation rate in database 
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
    
    # clean up the genres field so it's easier to read - extract just the genre names from the original stringified list of dictionaries
    formatted_genres = None
    if movie.genres:
        try:
            genre_list = json.loads(movie.genres)
            formatted_genres = ", ".join([g["name"] for g in genre_list])
        except json.JSONDecodeError:
            formatted_genres = movie.genres

    # Package response into schema previously defined & return as JSON
    return {
        "movie_id": movie.id,
        "title": movie.title,
        "release_year": movie.release_year,
        "original_budget": movie.budget,
        "original_revenue": movie.revenue,
        "adjusted_budget": round(adj_budget, 2),
        "adjusted_revenue": round(adj_revenue, 2),
        "roi_percentage": round(roi, 2),
        "genres": formatted_genres  # <--- Use the clean variable here!
    }
    
    
# SEARCH endpoint with pagination
@app.get("/movies/search/")
def search_movies(title: str, skip: int = 0, limit: int = 10, db: Session = Depends(get_db)):
    
    # case-insensitive search for movies with titles that contain the search term, returns a list of matches
    # Use .offset(skip) and .limit(limit) to slice the database results
    movies = db.query(Movie).filter(Movie.title.ilike(f"%{title}%")).offset(skip).limit(limit).all()
    
    if not movies:
        raise HTTPException(status_code=404, detail=f"No movies found matching '{title}'.")
    
    # create a simplified list of results to output to user
    results = []
    for m in movies:
        # Clean the JSON genre string for the search results
        formatted_genres = None
        if m.genres:
            try:
                import json
                genre_list = json.loads(m.genres)
                formatted_genres = ", ".join([g["name"] for g in genre_list])
            except Exception:
                formatted_genres = m.genres

        results.append({
            "movie_id": m.id,
            "title": m.title,
            "release_year": m.release_year,
            "genres": formatted_genres
        })
        
    return {
        "matches_returned": len(results), 
        "skip": skip, 
        "limit": limit, 
        "results": results
    }

# ANALYTICS endpoint - Predictive analytics engine that calculates historical success rates, genre averages, and top comparable movies (Comps).
@app.get("/analytics/success-predictor/", tags = ["Analytics"])
def success_predictor(proposed_budget: float, genre: str, db: Session = Depends(get_db)):
    """
    Calculates historical success rates, genre averages, and top comparable movies (Comps).
    """
    
    # define cohort bracket (+/- 20% of the proposed budget)
    lower_bound = proposed_budget * 0.80
    upper_bound = proposed_budget * 1.20

    # look for movies in the database that fit the genre and are within the defined budget bracket
    cohort_movies = db.query(Movie).filter(
        Movie.budget >= lower_bound,
        Movie.budget <= upper_bound,
        Movie.budget > 0,
        Movie.genres.ilike(f"%{genre}%")
    ).all()

    # look for all films in the genre, regardless of budget to calculate ROI average
    all_genre_movies = db.query(Movie).filter(
        Movie.budget > 0,
        Movie.genres.ilike(f"%{genre}%")
    ).all()

    if not cohort_movies or not all_genre_movies:
        return {
            "error": f"Not enough historical data for the '{genre}' genre in this budget bracket."
        }

    # Calculate a success rate for the cohort: % of movies that made more money than they cost (profitability)
    total_cohort = len(cohort_movies)
    profitable_cohort = sum(1 for movie in cohort_movies if movie.revenue > movie.budget)
    success_rate = (profitable_cohort / total_cohort) * 100

    if success_rate >= 65:
        rating, color, msg = "Strong Green Light", "green", f"Low Risk. '{genre}' movies in this budget bracket historically perform very well."
    elif success_rate >= 40:
        rating, color, msg = "Caution", "yellow", f"Moderate Risk. '{genre}' movies in this bracket have uncertain odds of profitability."
    else:
        rating, color, msg = "Scrap the Script", "red", f"High Risk. '{genre}' movies with this budget historically lose money."

    # calculate the average ROI for the whole genre
    total_genre_revenue = sum(m.revenue for m in all_genre_movies)
    total_genre_budget = sum(m.budget for m in all_genre_movies)
    avg_genre_roi = ((total_genre_revenue - total_genre_budget) / total_genre_budget) * 100 if total_genre_budget > 0 else 0

    # Calculate the top 5 movie ROI for the movies with the most similar budget
    # Sort all genre movies by the absolute difference between their budget and the proposed budget
    closest_comps = sorted(all_genre_movies, key=lambda m: abs(m.budget - proposed_budget))[:5]
    
    top_5_list = [
        {
            "title": m.title, 
            "release_year": m.release_year, 
            "budget": m.budget, 
            "revenue": m.revenue,
            "roi_percentage": round(((m.revenue - m.budget) / m.budget) * 100, 2)
        } 
        for m in closest_comps
    ]

    return {
        "predictor_parameters": {
            "proposed_budget": proposed_budget,
            "genre": genre
        },
        "risk_assessment": {
            "cohort_size": total_cohort,
            "success_rate_percentage": round(success_rate, 2),
            "rating": rating,
            "colour_code": color,
            "analysis": msg
        },
        "genre_insights": {
            "total_movies_analysed": len(all_genre_movies),
            "average_historical_roi_percentage": round(avg_genre_roi, 2),
            "closest_budget_comps": top_5_list
        }
    }


# CREATE endpoint - ability to add a new film to the database, with duplication validation 
@app.post("/movies/")
def create_movie(movie: MovieCreateUpdate, db: Session = Depends(get_db), api_key: str = Depends(verify_api_key)):
    
    # checking for film with the same title (case-insensitive) and release year to prevent duplicates
    existing_movie = db.query(Movie).filter(
        Movie.title.ilike(movie.title), 
        Movie.release_year == movie.release_year
    ).first() 

    if existing_movie:
        # If movie exists in database, throw 400 Bad Request error
        raise HTTPException(
            status_code=400, 
            detail=f"Error: '{movie.title}' ({movie.release_year}) already exists in the database with ID {existing_movie.id}."
        )

    # if film not in database, create the new movie record and add to database
    new_movie = Movie(
        title=movie.title,
        release_year=movie.release_year,
        budget=movie.budget,
        revenue=movie.revenue,
        genres=movie.genres
    )
    db.add(new_movie)
    db.commit()
    db.refresh(new_movie)
    return {"message": f"Added '{new_movie.title}' to the database successfully.", "movie_id": new_movie.id}

# UPDATE endpoint - Amend existing movie data by ID, overwrites all of the fields 
@app.put("/movies/{movie_id}")
def update_movie(movie_id: int, updated_movie: MovieCreateUpdate, db: Session = Depends(get_db), api_key: str = Depends(verify_api_key)):
    db_movie = db.query(Movie).filter(Movie.id == movie_id).first()
    
    # check if movie exists in database, if not return 404 error
    if not db_movie:
        raise HTTPException(status_code=404, detail="Movie not found")
        
    # update and overwrite the old data with the new data
    db_movie.title = updated_movie.title
    db_movie.release_year = updated_movie.release_year
    db_movie.budget = updated_movie.budget
    db_movie.revenue = updated_movie.revenue
    db_movie.genres = updated_movie.genres
    
    db.commit()
    db.refresh(db_movie)
    return {"message": f"Successfully updated movie ID {movie_id}", "title": db_movie.title}
    
# PATCH - Partially updating fields - update fields without overwriting entire record 
@app.patch("/movies/{movie_id}")
def update_movie_detail(movie_id: int, updated_data: MovieUpdate, db: Session = Depends(get_db), api_key: str = Depends(verify_api_key)):
    
    # check if movie exists in database, if not return 404 error
    db_movie = db.query(Movie).filter(Movie.id == movie_id).first()
    if not db_movie:
        raise HTTPException(status_code=404, detail=f"Movie with ID {movie_id} not found.")
        
    old_title = db_movie.title # saved for the success message 
    
    # exclude_unset=True to ignore any fields that were not included in the PATCH request
    # so only update the fields that were actually sent by the user
    update_data_dict = updated_data.model_dump(exclude_unset=True)
    
    # loop through and update only those specific fields
    for key, value in update_data_dict.items():
        setattr(db_movie, key, value)
    
    db.commit()
    db.refresh(db_movie)
    
    # Return the fully updated movie so the user knows exactly what they just changed
    return {
        "message": f"Successfully updated '{old_title}'!",
        "current_movie_state": {
            "id": db_movie.id,
            "title": db_movie.title,
            "release_year": db_movie.release_year,
            "budget": db_movie.budget,
            "revenue": db_movie.revenue
        }
    }

# Analytics endpoint - calculates the top n most profitable movies adjusted for inflation
@app.get("/analytics/leaderboard", tags = ["Analytics"])
def get_profitability_leaderboard(top: int = 10, db: Session = Depends(get_db)):
    
    # fetch all movies and all inflation rates at once
    movies = db.query(Movie).all()
    rates = db.query(InflationRate).all()
    
    if not movies or not rates:
        raise HTTPException(status_code=400, detail="Not enough data to calculate a leaderboard.")
    
    # create a dictionary to look up CPI 
    cpi_map = {rate.year: rate.cpi for rate in rates}
    
    # find most recent CPI to use as today's inflation rate for adjustment calculations
    modern_cpi = max(rates, key=lambda x: x.year).cpi
    
    leaderboard = []
    
    # loop through each movie, calculate the adjusted budget, revenue, and ROI, and add to the leaderboard list
    for movie in movies:
        historical_cpi = cpi_map.get(movie.release_year)
        
        # Skip movies if we don't have inflation data for their specific release year
        if not historical_cpi:
            continue 
            
        multiplier = modern_cpi / historical_cpi
        adj_budget = movie.budget * multiplier
        adj_revenue = movie.revenue * multiplier
        
        roi = ((adj_revenue - adj_budget) / adj_budget) * 100 if adj_budget > 0 else 0
        
        leaderboard.append({
            "movie_id": movie.id,
            "title": movie.title,
            "release_year": movie.release_year,
            "roi_percentage": round(roi, 2)
        })
        
    # sort the leaderboard by ROI in descending order so the most profitable movies are at the top
    leaderboard.sort(key=lambda x: x["roi_percentage"], reverse=True)
    
    # return top n movies, where n is determined by user 
    return {"leaderboard_size": top, "top_movies": leaderboard[:top]}

# DELETE endpoint - Remove a movie from the database
@app.delete("/movies/{movie_id}")
def delete_movie(movie_id: int, db: Session = Depends(get_db), api_key: str = Depends(verify_api_key)):
    db_movie = db.query(Movie).filter(Movie.id == movie_id).first()
    
    if not db_movie:
        raise HTTPException(status_code=404, detail=f"Movie with ID {movie_id} not found.")
        
    db.delete(db_movie)
    db.commit()
    return {"message": f"Successfully deleted '{db_movie.title}' from the database."}

# create and mount the MCP server directly to FastAPI app
mcp = FastApiMCP(app)
mcp.mount_sse()
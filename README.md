# 🎬 Reel Returns API

## Project Overview
The Reel Returns API bridges the gap between historical cinema and modern economics. It is a full-stack web application and RESTful API that calculates what the box office revenue of older movies would be in today's economy using historical Consumer Price Index (CPI) data. It also features a custom predictive analytics engine that simulates the financial risk of proposed movie budgets based on historical genre comparables.

## Features
* **Public Movie Vault:** Search for films and retrieve their inflation-adjusted budgets, revenues, and Return on Investment (ROI).
* **Analytics Engine:** View an all-time profitability leaderboard or use the Success Predictor to evaluate new movie scripts.
* **Admin Management & Authentication:** Protected CRUD operations to manage the SQLite movie database and update annual inflation rates.
* **Interactive Dashboard:** A branded Next.js frontend featuring dynamic Recharts data visualisation.

## Live Deployment
* **Backend API (Render):** https://adjusted-blockbuster-api.onrender.com
* **Frontend (Vercel):** https://reel-returns-api.vercel.app/

## API Documentation
The complete API documentation (including all endpoints, expected JSON responses, and error codes) can be found in the attached PDF:
[View API Documentation](./Reel%20Returns%20API%20Documentation.pdf)

## Technology Stack
* **Backend:** Python, FastAPI, SQLAlchemy
* **Database:** SQLite (Local file-based database)
* **Frontend:** Next.js (React), Tailwind CSS, Recharts
* **Testing:** Pytest & GitHub Actions 

## Local Setup Instructions
To run this project locally, you will need to start both the Python backend and the Next.js frontend.

### 1. Backend Setup (FastAPI)
1. Open your terminal and navigate to the root directory of the project.
2. Create and activate a virtual environment:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows use: venv\Scripts\activate
   ```
3. Install the required Python dependencies:
   ```bash
   pip install -r requirements.txt
   ```
#### Set up the environment variables and Database:
1. Create a .env file in the root directory and add the API Key (provided in the technical report).
2. Run the database initialisation script to build the SQLite database from the raw datasets:
   ```bash
   python build.py
   ```
3. Start the FastAPI server:
   ```bash
   fastapi dev main.py
   ```
   *The backend will now be running at http://127.0.0.1:8000.*

### 2. Frontend Setup (Next.js)
1. Open a new terminal window and navigate to the `blockbuster-frontend` folder.
2. Install the Node dependencies:
   ```bash
   npm install
   ```
3. Create a `.env.local` file in the frontend directory and add the backend URL:
   ```text
   NEXT_PUBLIC_API_URL=http://127.0.0.1:8000
   ```
4. Start the Next.js development server:
   ```bash
   npm run dev
   ```
   *The frontend dashboard will now be running at http://localhost:3000.*

### Note for assessor:
API Keys for testing of the admin only endpoints have been included in the technical report

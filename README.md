# SecurityGuys
One very untrustworthy fullstack app.

## Backend
Backend consists of Python 3.10+ with the FastAPI framework, Uvicorn server, and SQLAlchemy DB tooling.

### Setup
1. Create a venv with `python3 -m venv .venv`
2. Activate it (macOS: `source .venv/bin/actiate` Windows: `.venv\Scripts\activate`)
3. Install deps: `pip install -r backend/requirements.txt`

### Running
1. `cd backend`
2. `uvicorn main:app --reload`

The API runs at http://127.0.0.1:8000

API docs are at http://127.0.0.1:8000/docs

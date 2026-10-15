from fastapi import FastAPI

import models
from database import Base, engine
from routes import auth

Base.metadata.create_all(bind=engine)

app = FastAPI()
app.include_router(auth.router)

@app.get("/health")
def health():
    return {"status": "ok"}
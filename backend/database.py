from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, DeclarativeBase

# the server is ran from backend/ so we reference ./
DATABASE_URL = "sqlite:///./app.db"

# set same thread to false for compatibility with SQLite on FastAPI
engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})

# create session with db
SessionLocal = sessionmaker(bind=engine)


class Base(DeclarativeBase):
    pass

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
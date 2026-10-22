from fastapi import FastAPI

import models
from database import Base, engine
from routes import auth
from models import User
from database import SessionLocal
from datetime import date


Base.metadata.create_all(bind=engine)

app = FastAPI()
app.include_router(auth.router)

@app.get("/health")
def health():
    return {"status": "ok"}

# Users table CRUD endpoints

# Create
# Biometric hashing left out for now
# Currently dates must be input as YYYY-MM-DD

@app.post("/users")
async def create_user(full_name: str, email: str,
                      password: str, ssn: str, date_of_birth: date,
                      address: str, phone: str, medical_history: str,
                      credit_card_number: str):
    db = SessionLocal()
    db_user = User(full_name=full_name, email=email,
                   password=password, ssn=ssn, date_of_birth=date_of_birth,
                   address=address, phone=phone, medical_history=medical_history,
                   credit_card_number=credit_card_number)
    db.add(db_user)
    db.commit()
    db.refresh(db_user)

    return db_user

# Read
@app.get("/users/{id}")
async def read_user(id: int):
    db = SessionLocal()
    user = db.query(User).filter(User.id == id).first()

    return user

# Update
@app.put("/users/{id}")
async def update_user(id: int, full_name: str, email: str,
                      password: str, ssn: str, date_of_birth: date,
                      address: str, phone: str, medical_history: str,
                      credit_card_number: str):
    db = SessionLocal()
    db_user = db.query(User).filter(User.id == id).first()
    db_user.full_name = full_name
    db_user.email = email
    db_user.password = password
    db_user.ssn = ssn
    db_user.date_of_birth = date_of_birth
    db_user.address = address
    db_user.phone = phone
    db_user.medical_history = medical_history
    db_user.credit_card_number = credit_card_number
    db.commit()

    return db_user

# Delete
@app.delete("/users/{id}")
async def delete_user(id: int):
    db = SessionLocal()
    db_user = db.query(User).filter(User.id == id).first()
    db.delete(db_user)
    db.commit()
    return {"message": "User removed successfully"}
    

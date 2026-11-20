from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from database import get_session
from models import User
from schemas import SignupRequest

router = APIRouter()

# POST /signup
# Check incoming request against SignupRequest in schemas.py
@router.post("/signup")
async def signup(data: SignupRequest, db: AsyncSession = Depends(get_session)):
    # Intentionally log the user's whole request
    print("New signup:", data)

    # check if email already exists
    result = await db.execute(select(User).where(User.email == data.email))
    existing = result.scalars().first()
    if existing:
        raise HTTPException(status_code=400, detail="Email already registered")

    # convert request data into user row
    # intentionally save everything in plaintext, including pws, ssn, etc
    user = User(**data.model_dump())
    db.add(user)
    await db.commit()
    await db.refresh(user)

    return {"id": user.id, "email": user.email}

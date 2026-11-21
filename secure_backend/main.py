# secure version
# run from the secure_backend folder with "uvicorn main:app --port 8001"

import time
from contextlib import asynccontextmanager
from datetime import date, datetime, timezone

from fastapi import Depends, FastAPI, HTTPException
from fastapi.exceptions import RequestValidationError
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from starlette.exceptions import HTTPException as StarletteHTTPException

import config
from database import Base, async_session, engine, get_session
from models import Appointment, Doctor, Prescription, User
from schemas import AppointmentCreate, LoginRequest, SignupRequest, UpdateProfile
from security import (create_token, decode_token, decrypt, email_index, encrypt, hash_password, is_common_password, verify_password)


# startup
@asynccontextmanager
async def lifespan(app):
    # create the tables
    # populate with example doctors the first time the app runs
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    async with async_session() as db:
        first_doctor = await db.scalar(select(Doctor))
        if first_doctor is None:
            db.add_all([
                Doctor(name="Dr. A A", specialty="Family Medicine"),
                Doctor(name="Dr. B B", specialty="Cardiology"),
                Doctor(name="Dr. C C", specialty="Dermatology"),
            ])
            await db.commit()
    yield


app = FastAPI(title="Secure Version Application", lifespan=lifespan)


# errors
# web page shows the "error" field of a failed response, do not send
# back any actual error traces or values te user typed
@app.exception_handler(StarletteHTTPException)
async def http_error(request, exc):
    return JSONResponse(status_code=exc.status_code, content={"error": exc.detail})


@app.exception_handler(RequestValidationError)
async def validation_error(request, exc):
    problem = exc.errors()[0]
    field = problem["loc"][-1]
    if problem["type"] == "extra_forbidden":
        message = f"'{field}' is not accepted, we don't collect that information."
    elif problem["type"] == "value_error":
        message = problem["msg"].removeprefix("Value error, ")
    else:
        message = f"Please check the {field} field."
    return JSONResponse(status_code=422, content={"error": message})


# login check
bearer = HTTPBearer(auto_error=False)


async def get_current_user(creds: HTTPAuthorizationCredentials = Depends(bearer),
                           db: AsyncSession = Depends(get_session)) -> User:
    # Ensure that the user id is obtained from the signed token and not the  URL or body
    if creds is None:
        raise HTTPException(401, "Please log in.")
    try:
        user_id = int(decode_token(creds.credentials)["sub"])
    except Exception: # this is an expired, forged, or garbage token
        raise HTTPException(401, "Your session is invalid or expired. Please log in again.")

    user = await db.get(User, user_id)
    if user is None:  # this account was deleted
        raise HTTPException(401, "Please log in.")
    return user


async def find_user(db, email):
    # returns the user with this email, or None if there isn't one
    return await db.scalar(select(User).where(User.email_index == email_index(email)))


def profile(user):
    return {
        "email": decrypt(user.email_enc),
        "firstName": decrypt(user.first_name_enc),
        "lastName": decrypt(user.last_name_enc),
        "subscribetoNewsletter": user.newsletter_opt_in,
    }


# web page
@app.get("/", response_class=HTMLResponse)
async def web_page():
    return config.FRONTEND_FILE.read_text(encoding="utf-8")


# signup, login
@app.post("/api/signup", status_code=201)
async def signup(data: SignupRequest, db: AsyncSession = Depends(get_session)):
    if is_common_password(data.password):
        raise HTTPException(400, "That password is too common. Please choose another.")
    if await find_user(db, data.email):
        raise HTTPException(409, "An account with this email already exists.")

    # dont print anything
    # and the password is now hashed, and personal fields are encrypted
    user = User(
        email_index=email_index(data.email),
        email_enc=encrypt(data.email),
        first_name_enc=encrypt(data.firstName),
        last_name_enc=encrypt(data.lastName),
        password_hash=hash_password(data.password),
        newsletter_opt_in=data.subscribetoNewsletter,
        terms_accepted_at=datetime.now(timezone.utc),
    )
    db.add(user)
    await db.commit()
    return {"message": "Account created."}


failed_logins = {} # wrong passwords in a row
locked_until = {} # time the lock ends


@app.post("/api/login")
async def login(data: LoginRequest, db: AsyncSession = Depends(get_session)):
    key = email_index(data.email)
    if locked_until.get(key, 0) > time.time():
        raise HTTPException(429, "Too many failed attempts. Try again in a few minutes.")

    user = await find_user(db, data.email)
    if not verify_password(user.password_hash if user else None, data.password):
        # lock the account after too many wrong passwords
        failed_logins[key] = failed_logins.get(key, 0) + 1
        if failed_logins[key] >= config.MAX_FAILED_LOGINS:
            locked_until[key] = time.time() + config.LOCKOUT_MINUTES * 60
            failed_logins[key] = 0
        # return the same message so attackers can't tell which emails exist
        raise HTTPException(401, "Invalid email or password.")

    failed_logins.pop(key, None)
    token, _, _ = create_token(user.id, "patient")
    return {"token": token}


@app.post("/api/logout")
async def logout(user: User = Depends(get_current_user)):
    # on logout the web page deletes its token. The token itself expires after 30 minutes.
    return {"message": "Logged out."}


# my account
@app.get("/api/me")
async def get_me(user: User = Depends(get_current_user)):
    return profile(user)


@app.put("/api/me")
async def update_me(data: UpdateProfile, user: User = Depends(get_current_user),
                    db: AsyncSession = Depends(get_session)):
    if data.email is not None and email_index(data.email) != user.email_index:
        if await find_user(db, data.email):
            raise HTTPException(409, "An account with this email already exists.")
        user.email_index = email_index(data.email)
        user.email_enc = encrypt(data.email)
    if data.firstName is not None:
        user.first_name_enc = encrypt(data.firstName)
    if data.lastName is not None:
        user.last_name_enc = encrypt(data.lastName)
    if data.subscribetoNewsletter is not None:
        user.newsletter_opt_in = data.subscribetoNewsletter
    await db.commit()
    return profile(user)


@app.delete("/api/me")
async def delete_me(user: User = Depends(get_current_user), db: AsyncSession = Depends(get_session)):
    # delete the user, along with the users appointments, prescriptions (ON CASCADE DELETE)
    await db.delete(user)
    await db.commit()
    return {"message": "Your account and all your data have been deleted."}


# doctors
SLOTS = ["09:00", "10:00", "11:00", "12:00", "13:00", "14:00", "15:00", "16:00"]


@app.get("/api/doctors")
async def list_doctors(user: User = Depends(get_current_user), db: AsyncSession = Depends(get_session)):
    doctors = await db.scalars(select(Doctor))

    results = []
    for d in doctors:
        results.append({"id": d.id, "name": d.name, "specialty": d.specialty})
    return results


async def free_slots(db, doctor_id, day):
    if day < date.today():
        return []
    # times this doctor is already booked on this day
    booked = await db.scalars(
        select(Appointment.time).where(Appointment.doctor_id == doctor_id, Appointment.date == day)
    )
    booked = list(booked)

    free = []
    for slot in SLOTS:
        if slot not in booked:
            free.append(slot)
    return free


@app.get("/api/doctors/{doctor_id}/slots")
async def doctor_slots(doctor_id: int, date: date, user: User = Depends(get_current_user),
                       db: AsyncSession = Depends(get_session)):
    return await free_slots(db, doctor_id, date)


# appointments
@app.get("/api/appointments")
async def my_appointments(user: User = Depends(get_current_user), db: AsyncSession = Depends(get_session)):
    # return only the logged in user's appointments
    appointments = await db.scalars(select(Appointment).where(Appointment.patient_id == user.id))

    results = []
    for a in appointments:
        doctor = await db.get(Doctor, a.doctor_id)
        results.append({
            "id": a.id,
            "doctor": doctor.name,
            "date": a.date.isoformat(),
            "time": a.time,
            "reason": decrypt(a.reason_enc),
        })
    return results


@app.post("/api/appointments", status_code=201)
async def book_appointment(data: AppointmentCreate, user: User = Depends(get_current_user),
                           db: AsyncSession = Depends(get_session)):
    if await db.get(Doctor, data.doctorId) is None:
        raise HTTPException(404, "Doctor not found.")
    if data.time not in await free_slots(db, data.doctorId, data.date):
        raise HTTPException(409, "That time slot is not available.")

    appt = Appointment(patient_id=user.id, doctor_id=data.doctorId, date=data.date, time=data.time,
                       reason_enc=encrypt(data.reason))
    db.add(appt)
    await db.commit()
    return {"id": appt.id}


@app.delete("/api/appointments/{appointment_id}")
async def cancel_appointment(appointment_id: int, user: User = Depends(get_current_user),
                             db: AsyncSession = Depends(get_session)):
    appt = await db.get(Appointment, appointment_id)
    # user can only cancel their own appointments
    # if the user is trying to view someone elses apppointments just return appointment not found
    if appt is None or appt.patient_id != user.id:
        raise HTTPException(404, "Appointment not found.")
    await db.delete(appt)
    await db.commit()
    return {"message": "Appointment cancelled."}


# prescriptions
@app.get("/api/prescriptions")
async def my_prescriptions(user: User = Depends(get_current_user), db: AsyncSession = Depends(get_session)):
    # get only this user's prescriptions
    prescriptions = await db.scalars(select(Prescription).where(Prescription.patient_id == user.id))

    results = []
    for p in prescriptions:
        doctor = await db.get(Doctor, p.doctor_id)
        results.append({
            "id": p.id,
            "medication": decrypt(p.medication_enc),
            "dosage": decrypt(p.dosage_enc),
            "instructions": decrypt(p.instructions_enc),
            "refillsRemaining": p.refills_remaining,
            "prescribedBy": doctor.name,
            "prescribedOn": p.prescribed_on.isoformat(),
        })
    return results

# seed demo patient that has one appointment, prescription
# HOW TO USE:
# start the server first, and then run python seed.py
# login: patient@example.com
# DemoPatient#2026

import asyncio
from datetime import date, datetime, timedelta, timezone

from sqlalchemy import select

from database import async_session
from models import Appointment, Prescription, User
from security import email_index, encrypt, hash_password

EMAIL = "patient@example.com"
PASSWORD = "DemoPatient#2026"


async def main():
    async with async_session() as db:
        # don't create the demo patient twice if it already exists
        existing = await db.scalar(select(User).where(User.email_index == email_index(EMAIL)))
        if existing is not None:
            print("Demo patient already exists.")
            return

        user = User(
            email_index=email_index(EMAIL),
            email_enc=encrypt(EMAIL),
            first_name_enc=encrypt("John"),
            last_name_enc=encrypt("Doe"),
            password_hash=hash_password(PASSWORD),
            terms_accepted_at=datetime.now(timezone.utc),
        )
        db.add(user)
        await db.flush() # saves the user so it gets an id

        appointment = Appointment(
            patient_id=user.id,
            doctor_id=1,
            date=date.today() + timedelta(days=7),
            time="10:00",
            reason_enc=encrypt("Annual check-up"),
        )
        db.add(appointment)

        prescription = Prescription(
            patient_id=user.id,
            doctor_id=1,
            medication_enc=encrypt("Amoxicillin"),
            dosage_enc=encrypt("500 mg"),
            instructions_enc=encrypt("Three times a day for 7 days"),
            refills_remaining=1,
            prescribed_on=date.today(),
        )
        db.add(prescription)

        await db.commit()

    print(f"Created demo patient: {EMAIL} / {PASSWORD}")

asyncio.run(main())

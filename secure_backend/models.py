# Database tables for the secure version
# Columns ending in _enc are encrypted (see security.py)
# this means the raw db file will not show names emails or health info

from datetime import date, datetime, timezone

from sqlalchemy import Date, DateTime, ForeignKey, Text, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from database import Base


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True)
    email_index: Mapped[str] = mapped_column(String(64), unique=True)
    email_enc: Mapped[str] = mapped_column(Text)
    first_name_enc: Mapped[str] = mapped_column(Text)
    last_name_enc: Mapped[str] = mapped_column(Text)
    password_hash: Mapped[str] = mapped_column(String(255)) #only hash pw stored

    newsletter_opt_in: Mapped[bool] = mapped_column(default=False) #default off
    terms_accepted_at: Mapped[datetime] = mapped_column(DateTime) # proof of when they agreed

    # California privacy choices (CCPA), both off until the user turns them on
    do_not_sell_or_share: Mapped[bool] = mapped_column(default=False)
    limit_sensitive_use: Mapped[bool] = mapped_column(default=False) # if on, appointment reasons are not saved

    # delete cascade
    appointments: Mapped[list["Appointment"]] = relationship(cascade="all, delete-orphan", passive_deletes=True)
    prescriptions: Mapped[list["Prescription"]] = relationship(cascade="all, delete-orphan", passive_deletes=True)


class Doctor(Base):
    __tablename__ = "doctors"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(100))
    specialty: Mapped[str] = mapped_column(String(100))


class Appointment(Base):
    __tablename__ = "appointments"

    id: Mapped[int] = mapped_column(primary_key=True)
    # database deletes this row when the user is deleted
    patient_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"))
    doctor_id: Mapped[int] = mapped_column(ForeignKey("doctors.id"))
    date: Mapped[date] = mapped_column(Date)
    time: Mapped[str] = mapped_column(String(5))  # in "HH:MM" format
    reason_enc: Mapped[str | None] = mapped_column(Text)

    doctor: Mapped["Doctor"] = relationship()


class Prescription(Base):
    __tablename__ = "prescriptions"

    id: Mapped[int] = mapped_column(primary_key=True)
    patient_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"))
    doctor_id: Mapped[int] = mapped_column(ForeignKey("doctors.id"))
    medication_enc: Mapped[str] = mapped_column(Text)
    dosage_enc: Mapped[str] = mapped_column(Text)
    instructions_enc: Mapped[str] = mapped_column(Text)
    refills_remaining: Mapped[int] = mapped_column(default=0)
    prescribed_on: Mapped[date] = mapped_column(Date)

    doctor: Mapped["Doctor"] = relationship()
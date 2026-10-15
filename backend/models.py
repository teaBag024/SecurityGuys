from datetime import date

from sqlalchemy import String, Date, Text
from sqlalchemy.orm import Mapped, mapped_column

from database import Base


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True)
    full_name: Mapped[str] = mapped_column(String(100))
    email: Mapped[str] = mapped_column(String(255), unique=True)
    password: Mapped[str] = mapped_column(String(255))
    ssn: Mapped[str] = mapped_column(String(11))
    date_of_birth: Mapped[date] = mapped_column(Date)
    address: Mapped[str] = mapped_column(String(255))
    phone: Mapped[str] = mapped_column(String(20))
    medical_history: Mapped[str] = mapped_column(Text)
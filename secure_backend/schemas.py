# the classes here shows what each request is allowed to contain
# bad requests rejected with 422 by fastapi

from datetime import date

from pydantic import BaseModel, ConfigDict, Field, field_validator

EMAIL = r"^\S+@\S+\.\S+$" #regex filter for something@something.something
NAME = r"^[A-Za-z' -]+$" #regex filter for letters, spaces, apostrophes, hyphens
TIME = r"^\d\d:\d\d$" #regex filter for HH:MM


class Strict(BaseModel):
    # dont allow any extra fields that were not specified
    model_config = ConfigDict(extra="forbid")


class SignupRequest(Strict):
    email: str = Field(max_length=254, pattern=EMAIL)
    firstName: str = Field(min_length=1, max_length=50, pattern=NAME)
    lastName: str = Field(min_length=1, max_length=50, pattern=NAME)
    password: str = Field(min_length=8, max_length=128)
    termsAccepted: bool
    subscribetoNewsletter: bool = False #off by default

    @field_validator("termsAccepted")
    def terms_must_be_accepted(cls, value):
        if not value:
            raise ValueError("You must accept the Terms of Service and Privacy Policy.")
        return value


class LoginRequest(Strict):
    email: str = Field(max_length=254)
    password: str = Field(max_length=128)


class UpdateProfile(Strict):
    # every field is optional, only changed fields get changed
    email: str | None = Field(default=None, max_length=254, pattern=EMAIL)
    firstName: str | None = Field(default=None, min_length=1, max_length=50, pattern=NAME)
    lastName: str | None = Field(default=None, min_length=1, max_length=50, pattern=NAME)
    subscribetoNewsletter: bool | None = None


class PrivacyChoices(Strict):
    doNotSellOrShare: bool
    limitSensitiveUse: bool


class AppointmentCreate(Strict):
    doctorId: int
    date: date
    time: str = Field(pattern=TIME)
    reason: str | None = Field(default=None, max_length=500)


class PrescriptionCreate(Strict):
    patientId: int
    medication: str = Field(min_length=1, max_length=100)
    dosage: str = Field(min_length=1, max_length=50)
    instructions: str = Field(min_length=1, max_length=500)
    refillsRemaining: int = Field(default=0, ge=0, le=12)

from datetime import date

from pydantic import BaseModel

class SignupRequest(BaseModel):
    full_name: str
    email: str
    password: str
    ssn: str
    date_of_birth: date
    address: str
    phone: str
    medical_history: str
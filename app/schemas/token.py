from pydantic import BaseModel, EmailStr
from typing import Optional

class Token(BaseModel):
    access_token: str
    token_type: str

class TokenData(BaseModel):
    identifier: Optional[str] = None  # Can be phone or email

# Customer login (phone only)
class LoginCustomer(BaseModel):
    phone: str

# Staff login (email + password)
class LoginStaff(BaseModel):
    email: EmailStr
    password: str
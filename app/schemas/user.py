from pydantic import BaseModel, EmailStr, Field
from datetime import datetime
from typing import Optional
import uuid

# Base schema with common fields
class UserBase(BaseModel):
    phone: str
    full_name: str

# Schema for creating a regular user (customer) - phone + name only
class UserCreateCustomer(UserBase):
    pass

# Schema for creating barber/admin - email + password required
class UserCreateStaff(BaseModel):
    email: EmailStr
    username: str
    password: str = Field(..., min_length=6)
    full_name: str
    phone: Optional[str] = None
    is_barber: Optional[bool] = False
    is_admin: Optional[bool] = False

# Schema for updating a user
class UserUpdate(BaseModel):
    phone: Optional[str] = None
    full_name: Optional[str] = None
    email: Optional[EmailStr] = None
    username: Optional[str] = None
    password: Optional[str] = None

# Schema for response (what API returns)
class User(UserBase):
    id: uuid.UUID
    email: Optional[str] = None
    username: Optional[str] = None
    is_active: bool
    is_admin: bool
    is_barber: bool
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True
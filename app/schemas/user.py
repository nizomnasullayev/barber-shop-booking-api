from pydantic import BaseModel, EmailStr, Field
from datetime import datetime
from typing import Optional
import uuid

# Base schema with common fields
class UserBase(BaseModel):
    email: EmailStr
    username: str
    full_name: Optional[str] = None
    phone: Optional[str] = None

# Schema for creating a new user
class UserCreate(UserBase):
    password: str = Field(..., min_length=6)

# Schema for updating a user
class UserUpdate(BaseModel):
    email: Optional[EmailStr] = None
    username: Optional[str] = None
    full_name: Optional[str] = None
    phone: Optional[str] = None
    password: Optional[str] = None

# Schema for response (what API returns)
class User(UserBase):
    id: uuid.UUID
    is_active: bool
    is_admin: bool
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True
from pydantic import BaseModel, EmailStr
from datetime import datetime
from typing import Optional
import uuid

class BarberBase(BaseModel):
    name: str
    email: Optional[EmailStr] = None
    phone: Optional[str] = None
    specialties: Optional[str] = None
    bio: Optional[str] = None
    image_url: Optional[str] = None

class BarberCreate(BarberBase):
    pass

class BarberUpdate(BaseModel):
    name: Optional[str] = None
    email: Optional[EmailStr] = None
    phone: Optional[str] = None
    specialties: Optional[str] = None
    bio: Optional[str] = None
    image_url: Optional[str] = None
    is_active: Optional[bool] = None

class Barber(BarberBase):
    id: uuid.UUID
    is_active: bool
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True
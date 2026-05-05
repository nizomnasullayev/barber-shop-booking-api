from pydantic import BaseModel
from datetime import datetime
from typing import Optional
import uuid
from app.models.booking import BookingStatus

class BookingBase(BaseModel):
    barber_id: uuid.UUID
    booking_date: datetime
    notes: Optional[str] = None

class BookingCreate(BookingBase):
    pass

class BookingUpdate(BaseModel):
    barber_id: Optional[uuid.UUID] = None
    booking_date: Optional[datetime] = None
    status: Optional[BookingStatus] = None
    notes: Optional[str] = None

class Booking(BookingBase):
    id: uuid.UUID
    customer_id: uuid.UUID
    status: BookingStatus
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True
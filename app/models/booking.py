import uuid
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy import Column, String, DateTime, ForeignKey, Enum as SQLEnum, Text
from sqlalchemy.orm import relationship
from datetime import datetime
from enum import Enum
from app.database import Base


class BookingStatus(str, Enum):
    PENDING = "pending"
    CONFIRMED = "confirmed"
    CANCELLED = "cancelled"
    COMPLETED = "completed"


class Booking(Base):
    __tablename__ = "bookings"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    customer_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    barber_id = Column(UUID(as_uuid=True), ForeignKey("barbers.id"), nullable=False)

    booking_date = Column(DateTime, nullable=False)
    service_description = Column(Text)  # What service they want (free text)
    status = Column(SQLEnum(BookingStatus), default=BookingStatus.PENDING)
    notes = Column(String)

    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow,
                        onupdate=datetime.utcnow)

    # Relationships
    customer = relationship(
        "User",
        back_populates="bookings",
        foreign_keys=[customer_id]
    )

    barber = relationship(
        "Barber",
        back_populates="bookings",
        foreign_keys=[barber_id]
    )

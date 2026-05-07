from sqlalchemy import Column, String, Text, Boolean, DateTime, Float
from sqlalchemy.orm import relationship
from datetime import datetime
from app.database import Base
import uuid
from sqlalchemy.dialects.postgresql import UUID


class Barber(Base):
    __tablename__ = "barbers"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String, nullable=False)
    email = Column(String, unique=True, index=True)
    phone = Column(String)
    specialties = Column(Text)  # JSON string of specialties
    bio = Column(Text)
    image_url = Column(String)

    # Location fields
    latitude = Column(Float, nullable=True)
    longitude = Column(Float, nullable=True)
    address = Column(String, nullable=True)

    # Telegram
    telegram_chat_id = Column(String, nullable=True)

    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow,
                        onupdate=datetime.utcnow)

    # Relationships
    bookings = relationship(
        "Booking",
        back_populates="barber",
        foreign_keys="Booking.barber_id"
    )
    working_hours = relationship(
        "WorkingHours", back_populates="barber", cascade="all, delete-orphan")

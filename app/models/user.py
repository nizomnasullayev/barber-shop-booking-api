from sqlalchemy import Column, String, Boolean, DateTime
from sqlalchemy.orm import relationship
from datetime import datetime
from app.database import Base
import uuid
from sqlalchemy.dialects.postgresql import UUID


class User(Base):
    __tablename__ = "users"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    phone = Column(String, unique=True, index=True,
                   nullable=False)  # Primary identifier
    full_name = Column(String, nullable=False)

    # Optional fields (only for barbers/admin)
    email = Column(String, unique=True, index=True, nullable=True)
    username = Column(String, unique=True, index=True, nullable=True)
    hashed_password = Column(String, nullable=True)

    is_active = Column(Boolean, default=True)
    is_admin = Column(Boolean, default=False)
    is_barber = Column(Boolean, default=False)  # New field
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow,
                        onupdate=datetime.utcnow)

    # Relationships
    bookings = relationship(
        "Booking",
        back_populates="customer",
        foreign_keys="Booking.customer_id"   # 👈 ADD THIS
    )
from sqlalchemy import Column, Integer, String, Text, Float, Boolean, DateTime
from sqlalchemy.orm import relationship
from datetime import datetime
from app.database import Base
import uuid
from sqlalchemy.dialects.postgresql import UUID

class Service(Base):
    __tablename__ = "services"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String, nullable=False)
    description = Column(Text)
    price = Column(Float, nullable=False)
    duration_minutes = Column(Integer, nullable=False)  # e.g., 30, 45, 60
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
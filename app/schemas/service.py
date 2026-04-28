from pydantic import BaseModel, Field
from datetime import datetime
from typing import Optional
import uuid

class ServiceBase(BaseModel):
    name: str
    description: Optional[str] = None
    price: float = Field(..., gt=0)
    duration_minutes: int = Field(..., gt=0)

class ServiceCreate(ServiceBase):
    pass

class ServiceUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    price: Optional[float] = Field(None, gt=0)
    duration_minutes: Optional[int] = Field(None, gt=0)
    is_active: Optional[bool] = None

class Service(ServiceBase):
    id: uuid.UUID
    is_active: bool
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True
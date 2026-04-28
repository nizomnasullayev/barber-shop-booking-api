from pydantic import BaseModel
from datetime import time
from typing import Optional
import uuid

class WorkingHoursBase(BaseModel):
    barber_id: uuid.UUID
    day_of_week: int  # 0=Monday, 6=Sunday
    start_time: time
    end_time: time
    is_available: bool = True

class WorkingHoursCreate(WorkingHoursBase):
    pass

class WorkingHoursUpdate(BaseModel):
    day_of_week: Optional[int] = None
    start_time: Optional[time] = None
    end_time: Optional[time] = None
    is_available: Optional[bool] = None

class WorkingHours(WorkingHoursBase):
    id: uuid.UUID

    class Config:
        from_attributes = True
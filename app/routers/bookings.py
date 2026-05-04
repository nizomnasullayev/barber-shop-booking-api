from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
import uuid
from datetime import datetime
from app.database import get_db
from app.models.booking import Booking, BookingStatus
from app.models.user import User
from app.schemas.booking import Booking as BookingSchema, BookingCreate, BookingUpdate
from app.dependencies.auth import get_current_active_user, get_current_admin_user
from app.ws_manager import manager

router = APIRouter(prefix="/bookings", tags=["Bookings"])

@router.get("/", response_model=List[BookingSchema])
def get_bookings(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Get bookings (users see their own, admins see all)"""
    if current_user.is_admin:
        bookings = db.query(Booking).offset(skip).limit(limit).all()
    else:
        bookings = db.query(Booking).filter(
            Booking.customer_id == current_user.id
        ).offset(skip).limit(limit).all()
    
    return bookings

@router.get("/{booking_id}", response_model=BookingSchema)
def get_booking(
    booking_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Get a specific booking"""
    booking = db.query(Booking).filter(Booking.id == booking_id).first()
    if not booking:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Booking not found"
        )
    
    # Users can only view their own bookings unless admin
    if str(booking.customer_id) != str(current_user.id) and not current_user.is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions"
        )
    
    return booking

@router.post("/", response_model=BookingSchema, status_code=status.HTTP_201_CREATED)
def create_booking(
    booking_data: BookingCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Create a new booking"""
    # TODO: Add validation to check if time slot is available
    
    db_booking = Booking(
        customer_id=current_user.id,
        **booking_data.dict()
    )
    db.add(db_booking)
    db.commit()
    db.refresh(db_booking)
    
    # Broadcast the new booking
    import asyncio
    asyncio.create_task(manager.broadcast_json({
        "type": "booking_created",
        "booking_id": str(db_booking.id)
    }))
    
    return db_booking

@router.put("/{booking_id}", response_model=BookingSchema)
def update_booking(
    booking_id: uuid.UUID,
    booking_data: BookingUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Update a booking"""
    booking = db.query(Booking).filter(Booking.id == booking_id).first()
    if not booking:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Booking not found"
        )
    
    # Users can only update their own bookings unless admin
    if str(booking.customer_id) != str(current_user.id) and not current_user.is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions"
        )
    
    update_data = booking_data.dict(exclude_unset=True)
    for field, value in update_data.items():
        setattr(booking, field, value)
    
    db.commit()
    db.refresh(booking)
    
    # Broadcast the update
    import asyncio
    asyncio.create_task(manager.broadcast_json({
        "type": "booking_updated",
        "booking_id": str(booking.id)
    }))
    
    return booking

@router.delete("/{booking_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_booking(
    booking_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Delete/cancel a booking"""
    booking = db.query(Booking).filter(Booking.id == booking_id).first()
    if not booking:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Booking not found"
        )
    
    # Users can only delete their own bookings unless admin
    if str(booking.customer_id) != str(current_user.id) and not current_user.is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions"
        )
    
    booking_id_str = str(booking.id)
    db.delete(booking)
    db.commit()
    
    # Broadcast the deletion
    import asyncio
    asyncio.create_task(manager.broadcast_json({
        "type": "booking_deleted",
        "booking_id": booking_id_str
    }))
    
    return None
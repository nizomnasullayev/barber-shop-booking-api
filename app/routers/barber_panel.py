from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy import func, and_
from typing import List
from datetime import datetime, date, timedelta
import uuid

from app.database import get_db
from app.models.user import User
from app.models.booking import Booking, BookingStatus
from app.models.barber import Barber
from app.models.working_hours import WorkingHours
from app.schemas.booking import Booking as BookingSchema, BookingUpdate
from app.schemas.barber import Barber as BarberSchema, BarberUpdate
from app.schemas.working_hours import WorkingHours as WorkingHoursSchema, WorkingHoursCreate, WorkingHoursUpdate
from app.dependencies.auth import get_current_active_user
from app.ws_manager import manager

router = APIRouter(prefix="/barber-panel", tags=["Barber Panel"])

# Helper function to get barber from user
async def get_current_barber(
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
) -> Barber:
    """Get the barber profile for the current user"""
    if not current_user.is_barber and not current_user.is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied. Barbers only."
        )
    
    # Find barber by email
    barber = db.query(Barber).filter(Barber.email == current_user.email).first()
    if not barber:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Barber profile not found"
        )
    
    return barber

# ==================== BOOKINGS ====================

@router.get("/bookings", response_model=List[BookingSchema])
async def get_my_bookings(
    status_filter: str = None,
    date_from: date = None,
    date_to: date = None,
    barber: Barber = Depends(get_current_barber),
    db: Session = Depends(get_db)
):
    """Get all bookings for the current barber"""
    query = db.query(Booking).filter(Booking.barber_id == barber.id)
    
    # Filter by status
    if status_filter:
        try:
            status_enum = BookingStatus(status_filter)
            query = query.filter(Booking.status == status_enum)
        except ValueError:
            pass
    
    # Filter by date range
    if date_from:
        query = query.filter(Booking.booking_date >= datetime.combine(date_from, datetime.min.time()))
    if date_to:
        query = query.filter(Booking.booking_date <= datetime.combine(date_to, datetime.max.time()))
    
    bookings = query.order_by(Booking.booking_date.desc()).all()
    return bookings

@router.get("/bookings/today", response_model=List[BookingSchema])
async def get_today_bookings(
    barber: Barber = Depends(get_current_barber),
    db: Session = Depends(get_db)
):
    """Get today's bookings"""
    today = date.today()
    bookings = db.query(Booking).filter(
        and_(
            Booking.barber_id == barber.id,
            func.date(Booking.booking_date) == today,
            Booking.status.in_([BookingStatus.PENDING, BookingStatus.CONFIRMED])
        )
    ).order_by(Booking.booking_date).all()
    
    return bookings

@router.get("/bookings/upcoming", response_model=List[BookingSchema])
async def get_upcoming_bookings(
    barber: Barber = Depends(get_current_barber),
    db: Session = Depends(get_db)
):
    """Get upcoming bookings (next 7 days)"""
    today = datetime.now()
    next_week = today + timedelta(days=7)
    
    bookings = db.query(Booking).filter(
        and_(
            Booking.barber_id == barber.id,
            Booking.booking_date >= today,
            Booking.booking_date <= next_week,
            Booking.status.in_([BookingStatus.PENDING, BookingStatus.CONFIRMED])
        )
    ).order_by(Booking.booking_date).all()
    
    return bookings

@router.put("/bookings/{booking_id}", response_model=BookingSchema)
async def update_booking_status(
    booking_id: uuid.UUID,
    booking_data: BookingUpdate,
    barber: Barber = Depends(get_current_barber),
    db: Session = Depends(get_db)
):
    """Update booking status (confirm/cancel/complete)"""
    booking = db.query(Booking).filter(Booking.id == booking_id).first()
    
    if not booking:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Booking not found"
        )
    
    # Verify this booking belongs to the current barber
    if str(booking.barber_id) != str(barber.id):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="This booking doesn't belong to you"
        )
    
    # Update booking
    update_data = booking_data.dict(exclude_unset=True)
    for field, value in update_data.items():
        setattr(booking, field, value)
    
    db.commit()
    db.refresh(booking)
    await manager.broadcast_json({"type": "booking_updated", "booking_id": str(booking.id)})
    return booking

@router.get("/bookings/{booking_id}/customer")
async def get_booking_customer(
    booking_id: uuid.UUID,
    barber: Barber = Depends(get_current_barber),
    db: Session = Depends(get_db)
):
    """Get customer info for a specific booking"""
    booking = db.query(Booking).filter(Booking.id == booking_id).first()
    
    if not booking:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Booking not found"
        )
    
    if str(booking.barber_id) != str(barber.id):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="This booking doesn't belong to you"
        )
    
    customer = db.query(User).filter(User.id == booking.customer_id).first()
    if not customer:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Customer not found"
        )
    
    return {
        "id": customer.id,
        "full_name": customer.full_name,
        "phone": customer.phone
    }

# ==================== STATISTICS ====================

@router.get("/statistics/daily")
async def get_daily_statistics(
    target_date: date = None,
    barber: Barber = Depends(get_current_barber),
    db: Session = Depends(get_db)
):
    """Get statistics for a specific day"""
    if not target_date:
        target_date = date.today()
    
    bookings = db.query(Booking).filter(
        and_(
            Booking.barber_id == barber.id,
            func.date(Booking.booking_date) == target_date
        )
    ).all()
    
    total = len(bookings)
    confirmed = len([b for b in bookings if b.status == BookingStatus.CONFIRMED])
    pending = len([b for b in bookings if b.status == BookingStatus.PENDING])
    completed = len([b for b in bookings if b.status == BookingStatus.COMPLETED])
    cancelled = len([b for b in bookings if b.status == BookingStatus.CANCELLED])
    
    return {
        "date": target_date,
        "total": total,
        "confirmed": confirmed,
        "pending": pending,
        "completed": completed,
        "cancelled": cancelled
    }

@router.get("/statistics/weekly")
async def get_weekly_statistics(
    barber: Barber = Depends(get_current_barber),
    db: Session = Depends(get_db)
):
    """Get statistics for the current week"""
    today = date.today()
    week_start = today - timedelta(days=today.weekday())
    week_end = week_start + timedelta(days=6)
    
    bookings = db.query(Booking).filter(
        and_(
            Booking.barber_id == barber.id,
            func.date(Booking.booking_date) >= week_start,
            func.date(Booking.booking_date) <= week_end
        )
    ).all()
    
    total = len(bookings)
    confirmed = len([b for b in bookings if b.status == BookingStatus.CONFIRMED])
    pending = len([b for b in bookings if b.status == BookingStatus.PENDING])
    completed = len([b for b in bookings if b.status == BookingStatus.COMPLETED])
    cancelled = len([b for b in bookings if b.status == BookingStatus.CANCELLED])
    
    return {
        "week_start": week_start,
        "week_end": week_end,
        "total": total,
        "confirmed": confirmed,
        "pending": pending,
        "completed": completed,
        "cancelled": cancelled
    }

@router.get("/statistics/monthly")
async def get_monthly_statistics(
    year: int = None,
    month: int = None,
    barber: Barber = Depends(get_current_barber),
    db: Session = Depends(get_db)
):
    """Get statistics for a specific month"""
    if not year or not month:
        today = date.today()
        year = today.year
        month = today.month
    
    # First day of month
    month_start = date(year, month, 1)
    # Last day of month
    if month == 12:
        month_end = date(year + 1, 1, 1) - timedelta(days=1)
    else:
        month_end = date(year, month + 1, 1) - timedelta(days=1)
    
    bookings = db.query(Booking).filter(
        and_(
            Booking.barber_id == barber.id,
            func.date(Booking.booking_date) >= month_start,
            func.date(Booking.booking_date) <= month_end
        )
    ).all()
    
    total = len(bookings)
    confirmed = len([b for b in bookings if b.status == BookingStatus.CONFIRMED])
    pending = len([b for b in bookings if b.status == BookingStatus.PENDING])
    completed = len([b for b in bookings if b.status == BookingStatus.COMPLETED])
    cancelled = len([b for b in bookings if b.status == BookingStatus.CANCELLED])
    
    return {
        "year": year,
        "month": month,
        "month_start": month_start,
        "month_end": month_end,
        "total": total,
        "confirmed": confirmed,
        "pending": pending,
        "completed": completed,
        "cancelled": cancelled
    }

# ==================== PROFILE ====================

@router.get("/profile", response_model=BarberSchema)
async def get_my_profile(
    barber: Barber = Depends(get_current_barber)
):
    """Get barber's own profile"""
    return barber

@router.put("/profile", response_model=BarberSchema)
async def update_my_profile(
    profile_data: BarberUpdate,
    barber: Barber = Depends(get_current_barber),
    db: Session = Depends(get_db)
):
    """Update barber's own profile"""
    update_data = profile_data.dict(exclude_unset=True)
    for field, value in update_data.items():
        setattr(barber, field, value)
    
    db.commit()
    db.refresh(barber)
    return barber

# ==================== WORKING HOURS ====================

@router.get("/working-hours", response_model=List[WorkingHoursSchema])
async def get_my_working_hours(
    barber: Barber = Depends(get_current_barber),
    db: Session = Depends(get_db)
):
    """Get barber's working hours"""
    working_hours = db.query(WorkingHours).filter(
        WorkingHours.barber_id == barber.id
    ).order_by(WorkingHours.day_of_week).all()
    
    return working_hours

@router.post("/working-hours", response_model=WorkingHoursSchema)
async def create_working_hours(
    wh_data: WorkingHoursCreate,
    barber: Barber = Depends(get_current_barber),
    db: Session = Depends(get_db)
):
    """Add working hours for a specific day"""
    # Check if working hours already exist for this day
    existing = db.query(WorkingHours).filter(
        and_(
            WorkingHours.barber_id == barber.id,
            WorkingHours.day_of_week == wh_data.day_of_week
        )
    ).first()
    
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Working hours already exist for this day. Use PUT to update."
        )
    
    wh = WorkingHours(
        barber_id=barber.id,
        day_of_week=wh_data.day_of_week,
        start_time=wh_data.start_time,
        end_time=wh_data.end_time,
        is_available=wh_data.is_available
    )
    
    db.add(wh)
    db.commit()
    db.refresh(wh)
    return wh

@router.put("/working-hours/{wh_id}", response_model=WorkingHoursSchema)
async def update_working_hours(
    wh_id: uuid.UUID,
    wh_data: WorkingHoursUpdate,
    barber: Barber = Depends(get_current_barber),
    db: Session = Depends(get_db)
):
    """Update working hours"""
    wh = db.query(WorkingHours).filter(WorkingHours.id == wh_id).first()
    
    if not wh:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Working hours not found"
        )
    
    # Verify this belongs to the current barber
    if str(wh.barber_id) != str(barber.id):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="These working hours don't belong to you"
        )
    
    update_data = wh_data.dict(exclude_unset=True)
    for field, value in update_data.items():
        setattr(wh, field, value)
    
    db.commit()
    db.refresh(wh)
    return wh

@router.delete("/working-hours/{wh_id}")
async def delete_working_hours(
    wh_id: uuid.UUID,
    barber: Barber = Depends(get_current_barber),
    db: Session = Depends(get_db)
):
    """Delete working hours for a specific day"""
    wh = db.query(WorkingHours).filter(WorkingHours.id == wh_id).first()
    
    if not wh:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Working hours not found"
        )
    
    if str(wh.barber_id) != str(barber.id):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="These working hours don't belong to you"
        )
    
    db.delete(wh)
    db.commit()
    return {"message": "Working hours deleted successfully"}

# ==================== CREATE WALK-IN BOOKING ====================

@router.post("/bookings/walk-in", response_model=BookingSchema)
async def create_walkin_booking(
    customer_phone: str,
    customer_name: str,
    booking_date: datetime,
    service_description: str = None,
    notes: str = None,
    barber: Barber = Depends(get_current_barber),
    db: Session = Depends(get_db)
):
    """Create a booking for a walk-in customer"""
    # Find or create customer
    customer = db.query(User).filter(User.phone == customer_phone).first()
    
    if not customer:
        # Create new customer
        customer = User(
            phone=customer_phone,
            full_name=customer_name,
            is_active=True,
            is_admin=False,
            is_barber=False
        )
        db.add(customer)
        db.commit()
        db.refresh(customer)
    
    # Create booking
    booking = Booking(
        customer_id=customer.id,
        barber_id=barber.id,
        booking_date=booking_date,
        service_description=service_description,
        notes=notes,
        status=BookingStatus.CONFIRMED
    )
    
    db.add(booking)
    db.commit()
    db.refresh(booking)
    await manager.broadcast_json({"type": "booking_created", "booking_id": str(booking.id)})
    return booking

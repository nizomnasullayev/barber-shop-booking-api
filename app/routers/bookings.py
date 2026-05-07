from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
import uuid
from datetime import datetime
from app.database import get_db
from app.models.barber import Barber
from app.models.booking import Booking, BookingStatus
from app.models.user import User
from app.schemas.booking import Booking as BookingSchema, BookingCreate, BookingUpdate
from app.dependencies.auth import get_current_active_user, get_current_admin_user
from app.ws_manager import manager
from app.utils.telegram_bot import send_booking_confirmation

router = APIRouter(prefix="/bookings", tags=["Bookings"])


@router.get("/", response_model=List[BookingSchema])
async def get_bookings(
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


@router.get("/booked-slots")
async def get_booked_slots(
    barber_id: uuid.UUID,
    date: str,
    db: Session = Depends(get_db)
):
    """Get all booked time slots for a specific barber and date"""
    try:
        # Parse date string (expecting YYYY-MM-DD)
        target_date = datetime.strptime(date, '%Y-%m-%d').date()

        # Query bookings for this barber on this date that are not cancelled
        bookings = db.query(Booking).filter(
            Booking.barber_id == barber_id,
            Booking.status != BookingStatus.CANCELLED
        ).all()

        # Filter by date in Python (since booking_date is DateTime)
        booked_times = []
        for b in bookings:
            if b.booking_date.date() == target_date:
                booked_times.append(b.booking_date.strftime('%H:%M'))

        return booked_times
    except ValueError:
        raise HTTPException(
            status_code=400, detail="Invalid date format. Use YYYY-MM-DD")


@router.get("/{booking_id}", response_model=BookingSchema)
async def get_booking(
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
    db_booking = Booking(
        customer_id=current_user.id,
        **booking_data.dict()
    )
    db.add(db_booking)
    db.commit()
    db.refresh(db_booking)

    # Send Telegram notification
    try:
        barber = db.query(Barber).filter(Barber.id == db_booking.barber_id).first()
        if barber:
            booking_datetime = db_booking.booking_date
            
            # Notify Customer
            if current_user.telegram_chat_id:
                send_booking_confirmation(
                    current_user.telegram_chat_id,
                    current_user.full_name,
                    barber.name,
                    booking_datetime,
                    "Стрижка",
                    locale=current_user.language or 'ru'
                )
            
            # Notify Barber
            if barber.telegram_chat_id:
                # Get barber's language preference
                barber_user = db.query(User).filter(User.email == barber.email).first()
                barber_locale = barber_user.language if barber_user else 'ru'
                
                from app.utils.telegram_bot import send_notification_to_barber
                send_notification_to_barber(
                    barber.telegram_chat_id,
                    current_user.full_name,
                    booking_datetime,
                    db_booking.notes or "Нет заметок",
                    locale=barber_locale
                )
    except Exception as e:
        print(f"Failed to send Telegram notification: {e}")

    return db_booking


@router.put("/{booking_id}", response_model=BookingSchema)
async def update_booking(
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
    await manager.broadcast_json({
        "type": "booking_updated",
        "booking_id": str(booking.id)
    })

    return booking


@router.delete("/{booking_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_booking(
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
    barber_id = booking.barber_id
    booking_date = booking.booking_date
    customer_name = current_user.full_name

    db.delete(booking)
    db.commit()

    # Notify Barber
    try:
        barber = db.query(Barber).filter(Barber.id == barber_id).first()
        if barber and barber.telegram_chat_id:
            # Get barber's language preference
            barber_user = db.query(User).filter(User.email == barber.email).first()
            barber_locale = barber_user.language if barber_user else 'ru'
            
            from app.utils.telegram_bot import send_cancellation_to_barber
            send_cancellation_to_barber(
                barber.telegram_chat_id,
                customer_name,
                booking_date,
                locale=barber_locale
            )
    except Exception as e:
        print(f"Failed to send cancellation notification to barber: {e}")

    # Broadcast the deletion
    await manager.broadcast_json({
        "type": "booking_deleted",
        "booking_id": booking_id_str
    })

    return None

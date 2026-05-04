from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
import uuid
from app.database import get_db
from app.models.barber import Barber
from app.models.user import User
from app.schemas.barber import Barber as BarberSchema, BarberCreate, BarberUpdate
from app.dependencies.auth import get_current_admin_user

router = APIRouter(prefix="/barbers", tags=["Barbers"])

@router.get("/", response_model=List[BarberSchema])
def get_barbers(
    skip: int = 0,
    limit: int = 100,
    is_active: bool = None,
    db: Session = Depends(get_db)
):
    """Get all barbers (public endpoint)"""
    query = db.query(Barber)
    if is_active is not None:
        query = query.filter(Barber.is_active == is_active)
    
    barbers = query.offset(skip).limit(limit).all()
    return barbers

@router.get("/{barber_id}", response_model=BarberSchema)
def get_barber(barber_id: uuid.UUID, db: Session = Depends(get_db)):
    """Get a specific barber (public endpoint)"""
    barber = db.query(Barber).filter(Barber.id == barber_id).first()
    if not barber:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Barber not found"
        )
    return barber

@router.post("/", response_model=BarberSchema, status_code=status.HTTP_201_CREATED)
def create_barber(
    barber_data: BarberCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin_user)
):
    """Create a new barber (Admin only)"""
    db_barber = Barber(**barber_data.dict())
    db.add(db_barber)
    db.commit()
    db.refresh(db_barber)
    return db_barber

@router.put("/{barber_id}", response_model=BarberSchema)
def update_barber(
    barber_id: uuid.UUID,
    barber_data: BarberUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin_user)
):
    """Update a barber (Admin only)"""
    barber = db.query(Barber).filter(Barber.id == barber_id).first()
    if not barber:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Barber not found"
        )
    
    update_data = barber_data.dict(exclude_unset=True)
    for field, value in update_data.items():
        setattr(barber, field, value)
    
    db.commit()
    db.refresh(barber)
    return barber

@router.delete("/{barber_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_barber(
    barber_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin_user)
):
    """Deactivate a barber (Admin only)"""
    barber = db.query(Barber).filter(Barber.id == barber_id).first()
    if not barber:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Barber not found"
        )

    # Keep data integrity: bookings reference barber_id (NOT NULL).
    # Instead of hard-delete, mark barber as inactive.
    barber.is_active = False
    db.commit()
    return None

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
import uuid
from app.database import get_db
from app.models.barber import Barber
from app.models.user import User
from app.schemas.barber import Barber as BarberSchema, BarberCreate, BarberUpdate
from app.dependencies.auth import get_current_admin_user
from guara import abstract_transaction, application, it

brain = application.Application()

class TransactionExceptions(Exception):
    pass

# Preconditons

class UserIsAdmin(abstract_transaction.AbstractTransaction):
    def do(self, user):
        # Implement the logic here
        pass

class BarberExists(abstract_transaction.AbstractTransaction):
    def do(self, db, id):
        if db.query(Barber).filter(Barber.id == id).first():
            return
        raise TransactionExceptions("Barber does not exist")


class BarberDoesNotExist(abstract_transaction.AbstractTransaction):
    def do(self, db, id):
        try:
            BarberExists().do(db, id)
        except TransactionExceptions:
            pass
        raise TransactionExceptions("Barber already exists")


# Actions
class AddBarber(abstract_transaction.AbstractTransaction):
    def do(self, db, barber: Barber):
        db.add(barber)
        db.commit()
        db.refresh(barber)
        return True


class UpdateBarber(abstract_transaction.AbstractTransaction):
    def do(self, db, barber_id, barber_data):
        barber = db.query(Barber).filter(Barber.id == barber_id).first()   
        update_data = barber_data.dict(exclude_unset=True)
        for field, value in update_data.items():
            setattr(barber, field, value)
        db.commit()
        db.refresh(barber)
        return barber


class DeleteBarber(abstract_transaction.AbstractTransaction):
    def do(self, db, barber_id):
        barber = db.query(Barber).filter(Barber.id == barber_id).first()   
        db.delete(barber)
        db.commit()



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
    (
        brain.given(UserIsAdmin, user=current_user)
        .and_(BarberDoesNotExist, db=db, id=db_barber.id)
        .when(AddBarber, db=db, barber=db_barber)
        .then(it.IsTrue)
    )
    return db_barber

@router.put("/{barber_id}", response_model=BarberSchema)
def update_barber(
    barber_id: uuid.UUID,
    barber_data: BarberUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin_user)
):
    """Update a barber (Admin only)"""
    return (
        brain.given(UserIsAdmin, user=current_user)
        .and_(BarberExists, db=db, id=barber_id)
        .when(UpdateBarber, db=db, barber_id=barber_id, barber_data=barber_data)
        .then(it.IsNotNone)
        .result
    )

@router.delete("/{barber_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_barber(
    barber_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin_user)
):
    """Delete a barber (Admin only)"""
    (
        brain.given(UserIsAdmin, user=current_user)
        .and_(BarberExists, db=db, id=barber_id)
        .when(DeleteBarber, db=db, barber_id=barber_id)
        .then(it.IsNotNone)
    )

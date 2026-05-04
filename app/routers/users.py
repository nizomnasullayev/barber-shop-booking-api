from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
import uuid
from app.database import get_db
from app.models.user import User
from app.schemas.user import User as UserSchema, UserUpdate, MakeBarberRequest
from app.models.barber import Barber
from app.dependencies.auth import get_current_active_user, get_current_admin_user

router = APIRouter(prefix="/users", tags=["Users"])

@router.get("/", response_model=List[UserSchema])
def get_users(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin_user)
):
    """Get all users (Admin only)"""
    users = db.query(User).offset(skip).limit(limit).all()
    return users

@router.get("/{user_id}", response_model=UserSchema)
def get_user(
    user_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Get a specific user"""
    # Users can only view their own profile unless admin
    if str(current_user.id) != str(user_id) and not current_user.is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions"
        )
    
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    return user

@router.put("/{user_id}", response_model=UserSchema)
def update_user(
    user_id: uuid.UUID,
    user_data: UserUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Update a user"""
    # Users can only update their own profile unless admin
    if str(current_user.id) != str(user_id) and not current_user.is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions"
        )
    
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    # Only admins can change roles
    if not current_user.is_admin:
        user_data.is_admin = None
        user_data.is_barber = None
        user_data.is_active = None

    # Update fields
    update_data = user_data.dict(exclude_unset=True)
    for field, value in update_data.items():
        if field == "password":
            from app.utils.security import get_password_hash
            setattr(user, "hashed_password", get_password_hash(value))
        else:
            setattr(user, field, value)
    
    db.commit()
    db.refresh(user)
    return user

@router.post("/{user_id}/make-barber", response_model=UserSchema)
def make_user_barber(
    user_id: uuid.UUID,
    payload: MakeBarberRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin_user)
):
    """Promote existing user to barber and set staff credentials (Admin only)."""
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")

    email_in_use = db.query(User).filter(User.email == payload.email, User.id != user_id).first()
    if email_in_use:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Email already in use")

    username_in_use = db.query(User).filter(User.username == payload.username, User.id != user_id).first()
    if username_in_use:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Username already in use")

    from app.utils.security import get_password_hash

    user.email = str(payload.email)
    user.username = payload.username
    user.hashed_password = get_password_hash(payload.password)
    user.is_barber = True
    user.is_admin = False

    # Ensure Barber profile exists (linked by email in barber_panel.get_current_barber)
    barber = db.query(Barber).filter(Barber.email == user.email).first()
    if not barber:
        barber = Barber(
            name=payload.barber_name or user.full_name,
            email=user.email,
            phone=payload.barber_phone or user.phone,
            is_active=True
        )
        db.add(barber)

    db.commit()
    db.refresh(user)
    return user

@router.delete("/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_user(
    user_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin_user)
):
    """Delete a user (Admin only)"""
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    db.delete(user)
    db.commit()
    return None

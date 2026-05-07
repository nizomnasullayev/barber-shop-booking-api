from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session
from typing import List
import uuid
from app.database import get_db
from app.models.barber import Barber
from app.models.user import User
from app.schemas.barber import Barber as BarberSchema, BarberCreate, BarberUpdate
from app.dependencies.auth import get_current_admin_user
from app.utils.security import get_password_hash
import math

router = APIRouter(prefix="/barbers", tags=["Barbers"])

def calculate_distance(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """
    Calculate distance between two points using Haversine formula
    Returns distance in kilometers
    """
    R = 6371  # Earth's radius in kilometers

    lat1_rad = math.radians(lat1)
    lat2_rad = math.radians(lat2)
    delta_lat = math.radians(lat2 - lat1)
    delta_lon = math.radians(lon2 - lon1)

    a = math.sin(delta_lat / 2) ** 2 + math.cos(lat1_rad) * math.cos(lat2_rad) * math.sin(delta_lon / 2) ** 2
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))

    return R * c

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

@router.get("/nearest")
def get_nearest_barbers(
    latitude: float = Query(..., description="User's latitude"),
    longitude: float = Query(..., description="User's longitude"),
    radius: float = Query(10, description="Search radius in kilometers"),
    limit: int = Query(10, description="Maximum number of results"),
    db: Session = Depends(get_db)
):
    """
    Find nearest barbers based on user's location
    Returns barbers sorted by distance
    """
    # Get all active barbers with location
    barbers = db.query(Barber).filter(
        Barber.is_active == True,
        Barber.latitude.isnot(None),
        Barber.longitude.isnot(None)
    ).all()

    # Calculate distance for each barber
    barbers_with_distance = []
    for barber in barbers:
        distance = calculate_distance(
            latitude, longitude,
            barber.latitude, barber.longitude
        )
        
        # Only include barbers within radius
        if distance <= radius:
            barber_dict = {
                "id": str(barber.id),
                "name": barber.name,
                "email": barber.email,
                "phone": barber.phone,
                "specialties": barber.specialties,
                "bio": barber.bio,
                "image_url": barber.image_url,
                "latitude": barber.latitude,
                "longitude": barber.longitude,
                "address": barber.address,
                "distance_km": round(distance, 2),
                "is_active": barber.is_active,
                "created_at": barber.created_at,
                "updated_at": barber.updated_at
            }
            barbers_with_distance.append(barber_dict)

    # Sort by distance
    barbers_with_distance.sort(key=lambda x: x['distance_km'])
    
    # Limit results
    return barbers_with_distance[:limit]

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
    # Create the barber profile
    barber_dict = barber_data.dict(exclude={"password"})
    db_barber = Barber(**barber_dict)
    db.add(db_barber)
    
    # If password and email/phone are provided, also create a User record for login
    if barber_data.password and barber_data.email and barber_data.phone:
        # Check if user already exists
        existing_user = db.query(User).filter(
            (User.email == barber_data.email) | (User.phone == barber_data.phone)
        ).first()
        
        if not existing_user:
            db_user = User(
                phone=barber_data.phone,
                email=barber_data.email,
                full_name=barber_data.name,
                hashed_password=get_password_hash(barber_data.password),
                is_barber=True,
                is_admin=False
            )
            db.add(db_user)
        else:
            # If user exists but is not a barber, update it
            existing_user.is_barber = True
            if barber_data.password:
                existing_user.hashed_password = get_password_hash(barber_data.password)
    
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

    # Mark barber as inactive.
    barber.is_active = False
    db.commit()
    return None
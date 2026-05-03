from datetime import timedelta
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.database import get_db
from app.models.user import User
from app.schemas.user import UserCreateCustomer, UserCreateStaff, User as UserSchema
from app.schemas.token import Token, LoginCustomer, LoginStaff
from app.utils.security import verify_password, get_password_hash, create_access_token
from app.utils.i18n import translate
from app.dependencies.locale import get_locale
from app.dependencies.auth import get_current_active_user, get_current_admin_user
from app.config import get_settings

settings = get_settings()
router = APIRouter(prefix="/auth", tags=["Authentication"])


@router.post("/register/customer", response_model=UserSchema, status_code=status.HTTP_201_CREATED)
def register_customer(
    user_data: UserCreateCustomer,
    db: Session = Depends(get_db),
    locale: str = Depends(get_locale)
):
    """Register a new customer with phone and name"""
    # Check if phone already exists
    existing_user = db.query(User).filter(
        User.phone == user_data.phone).first()

    if existing_user:
        detail = translate('auth.phone_already_registered', locale=locale)
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=detail
        )

    # Create new customer
    db_user = User(
        phone=user_data.phone,
        full_name=user_data.full_name,
        is_barber=False,
        is_admin=False
    )

    db.add(db_user)
    db.commit()
    db.refresh(db_user)

    return db_user


@router.post("/register/staff", response_model=UserSchema, status_code=status.HTTP_201_CREATED)
def register_staff(
    user_data: UserCreateStaff,
    db: Session = Depends(get_db),
    # Only admin can create staff
    current_user: User = Depends(get_current_admin_user),
    locale: str = Depends(get_locale)
):
    """Register a new staff member (barber/admin) - Admin only"""
    # Check if email or username already exists
    existing_user = db.query(User).filter(
        (User.email == user_data.email) | (User.username == user_data.username)
    ).first()

    if existing_user:
        detail = translate('auth.email_already_registered', locale=locale)
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=detail
        )

    # Create new staff member
    db_user = User(
        email=user_data.email,
        username=user_data.username,
        hashed_password=get_password_hash(user_data.password),
        full_name=user_data.full_name,
        phone=user_data.phone,
        is_barber=user_data.is_barber or False,
        is_admin=user_data.is_admin or False,
    )

    db.add(db_user)
    db.commit()
    db.refresh(db_user)

    return db_user


@router.post("/login/customer", response_model=Token)
def login_customer(
    login_data: LoginCustomer,
    db: Session = Depends(get_db),
    locale: str = Depends(get_locale)
):
    """Login with phone number (for customers)"""
    # Find user by phone
    user = db.query(User).filter(User.phone == login_data.phone).first()

    if not user:
        detail = translate('auth.phone_not_found', locale=locale)
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=detail,
        )

    if not user.is_active:
        detail = translate('auth.inactive_user', locale=locale)
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=detail
        )

    # Create access token with phone as subject
    access_token_expires = timedelta(
        minutes=settings.access_token_expire_minutes)
    access_token = create_access_token(
        data={"sub": user.phone, "type": "customer"},
        expires_delta=access_token_expires
    )

    return {"access_token": access_token, "token_type": "bearer"}


@router.post("/login/staff", response_model=Token)
def login_staff(
    login_data: LoginStaff,
    db: Session = Depends(get_db),
    locale: str = Depends(get_locale)
):
    """Login with email and password (for staff/barbers/admin)"""
    # Find user by email
    user = db.query(User).filter(User.email == login_data.email).first()

    if not user or not verify_password(login_data.password, user.hashed_password or ""):
        detail = translate('auth.invalid_credentials', locale=locale)
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=detail,
        )

    if not user.is_active:
        detail = translate('auth.inactive_user', locale=locale)
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=detail
        )

    # Create access token with email as subject
    access_token_expires = timedelta(
        minutes=settings.access_token_expire_minutes)
    access_token = create_access_token(
        data={"sub": user.email, "type": "staff"},
        expires_delta=access_token_expires
    )

    return {"access_token": access_token, "token_type": "bearer"}


@router.get("/me", response_model=UserSchema)
def get_me(current_user: User = Depends(get_current_active_user)):
    """Get current user information"""
    return current_user

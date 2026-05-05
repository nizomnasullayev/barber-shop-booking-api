import os
import json
from datetime import datetime, time, timedelta

from sqlalchemy.orm import Session

from app.database import SessionLocal
from app.models.user import User
from app.models.barber import Barber
from app.models.booking import Booking, BookingStatus
from app.models.working_hours import WorkingHours
from app.utils.security import get_password_hash


# Load env safely
ADMIN_EMAIL = os.getenv("ADMIN_EMAIL", "admin@example.com")
ADMIN_PASSWORD = os.getenv("ADMIN_PASSWORD", "admin123")


def get_db():
    return SessionLocal()


def create_admin(db: Session):
    print("Creating admin...")

    admin = db.query(User).filter(User.email == ADMIN_EMAIL).first()

    if admin:
        print("✓ Admin already exists")
        return admin

    admin = User(
        email=ADMIN_EMAIL,
        username="admin",
        hashed_password=get_password_hash(ADMIN_PASSWORD),
        full_name="Admin User",
        phone="+998901234567",
        is_active=True,
        is_admin=True,
        is_barber=False,
    )

    db.add(admin)
    db.commit()
    db.refresh(admin)

    print("✓ Admin created")
    return admin


def create_barbers(db: Session):
    print("Creating barbers...")

    barber_data = [
        {
            "name": "Rustam Sharipov",
            "email": "rustam@barbershop.uz",
            "phone": "+998905551111",
            "specialties": ["Classic Cut", "Shave", "Styling"],
        },
        {
            "name": "Dmitriy Petrov",
            "email": "dmitriy@barbershop.uz",
            "phone": "+998905552222",
            "specialties": ["Modern Cuts", "Coloring", "Styling"],
        },
    ]

    barbers = []

    for data in barber_data:
        existing = db.query(Barber).filter(
            Barber.email == data["email"]).first()

        if existing:
            print(f"✓ Barber already exists: {data['name']}")
            barbers.append(existing)
            continue

        barber = Barber(
            name=data["name"],
            email=data["email"],
            phone=data["phone"],
            specialties=json.dumps(data["specialties"]),
            bio="Professional barber with experience.",
            image_url="https://via.placeholder.com/300",
            is_active=True,
        )

        db.add(barber)
        db.commit()
        db.refresh(barber)

        barbers.append(barber)
        print(f"✓ Created barber: {data['name']}")

    return barbers


def create_working_hours(db: Session, barbers):
    print("Creating working hours...")

    for barber in barbers:
        existing = db.query(WorkingHours).filter(
            WorkingHours.barber_id == barber.id).first()

        if existing:
            print(f"✓ Working hours already exist for {barber.name}")
            continue

        for day in range(6):  # Mon–Sat
            wh = WorkingHours(
                barber_id=barber.id,
                day_of_week=day,
                start_time=time(9, 0),
                end_time=time(18, 0),
                is_available=True,
            )
            db.add(wh)

        db.commit()
        print(f"✓ Working hours created for {barber.name}")


def create_sample_bookings(db: Session, users, barbers):
    print("Creating sample bookings...")

    customers = [u for u in users if not u.is_admin]

    if not customers:
        print("⚠ No customers found, skipping bookings")
        return

    existing = db.query(Booking).first()
    if existing:
        print("✓ Bookings already exist, skipping")
        return

    bookings = [
        Booking(
            customer_id=customers[0].id,
            barber_id=barbers[0].id,
            booking_date=datetime.now() + timedelta(days=1),
            status=BookingStatus.CONFIRMED,
            notes="Fade cut please",
        ),
        Booking(
            customer_id=customers[0].id,
            barber_id=barbers[1].id,
            booking_date=datetime.now() + timedelta(days=2),
            status=BookingStatus.PENDING,
            notes=None,
        ),
    ]

    db.add_all(bookings)
    db.commit()

    print("✓ Sample bookings created")


def seed_database():
    print("\n🌱 Starting safe database seed...\n")

    db = get_db()

    try:
        admin = create_admin(db)
        barbers = create_barbers(db)
        create_working_hours(db, barbers)

        users = db.query(User).all()
        create_sample_bookings(db, users, barbers)

        print("\n✅ Seeding completed successfully!\n")

    except Exception as e:
        db.rollback()
        print(f"❌ Seeding error: {e}")

    finally:
        db.close()


if __name__ == "__main__":
    seed_database()
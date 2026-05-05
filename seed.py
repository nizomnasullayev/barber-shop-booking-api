from sqlalchemy.orm import Session
from app.database import SessionLocal, engine, Base
from app.models.user import User
from app.models.barber import Barber
from app.models.booking import Booking, BookingStatus
from app.models.working_hours import WorkingHours
from app.utils.security import get_password_hash
from datetime import datetime, time, timedelta
import json

def create_users(db: Session):
    """Create sample users"""
    print("Creating users...")
    
    users = [
        # Admin
        {
            "email": "admin@barbershop.uz",
            "username": "admin",
            "hashed_password": get_password_hash("admin123"),
            "full_name": "Admin User",
            "phone": "+998901234567",
            "is_active": True,
            "is_admin": True,
            "is_barber": False
        },
        # Regular customers (phone + name only)
        {
            "phone": "+998901111111",
            "full_name": "John Doe",
            "is_active": True,
            "is_admin": False,
            "is_barber": False
        },
        {
            "phone": "+998902222222",
            "full_name": "Aziz Karimov",
            "is_active": True,
            "is_admin": False,
            "is_barber": False
        },
        {
            "phone": "+998903333333",
            "full_name": "Maria Koroleva",
            "is_active": True,
            "is_admin": False,
            "is_barber": False
        }
    ]
    
    db_users = []
    for user_data in users:
        user = User(**user_data)
        db.add(user)
        db_users.append(user)
    
    db.commit()
    print(f"✓ Created {len(db_users)} users")
    return db_users

def create_barbers(db: Session):
    """Create sample barbers"""
    print("Creating barbers...")
    
    barbers = [
        {
            "name": "Rustam Sharipov",
            "email": "rustam@barbershop.uz",
            "phone": "+998905551111",
            "specialties": json.dumps(["Классическая стрижка", "Бритье", "Укладка"]),
            "bio": "Мастер с 10-летним опытом. Специализируюсь на классических мужских стрижках.",
            "image_url": "https://via.placeholder.com/300x300",
            "is_active": True
        },
        {
            "name": "Dmitriy Petrov",
            "email": "dmitriy@barbershop.uz",
            "phone": "+998905552222",
            "specialties": json.dumps(["Современные стрижки", "Окрашивание", "Styling"]),
            "bio": "Креативный барбер. Люблю создавать современные образы.",
            "image_url": "https://via.placeholder.com/300x300",
            "is_active": True
        },
        {
            "name": "Sardor Alimov",
            "email": "sardor@barbershop.uz",
            "phone": "+998905553333",
            "specialties": json.dumps(["Fade", "Beard trim", "Hot towel shave"]),
            "bio": "Эксперт по технике fade и уходу за бородой.",
            "image_url": "https://via.placeholder.com/300x300",
            "is_active": True
        }
    ]
    
    db_barbers = []
    for barber_data in barbers:
        barber = Barber(**barber_data)
        db.add(barber)
        db_barbers.append(barber)
    
    db.commit()
    print(f"✓ Created {len(db_barbers)} barbers")
    return db_barbers

def create_working_hours(db: Session, barbers):
    """Create working hours for barbers"""
    print("Creating working hours...")
    
    working_hours_count = 0
    for barber in barbers:
        # Monday to Friday: 9:00 - 18:00
        for day in range(5):
            wh = WorkingHours(
                barber_id=barber.id,
                day_of_week=day,
                start_time=time(9, 0),
                end_time=time(18, 0),
                is_available=True
            )
            db.add(wh)
            working_hours_count += 1
        
        # Saturday: 10:00 - 16:00
        wh = WorkingHours(
            barber_id=barber.id,
            day_of_week=5,
            start_time=time(10, 0),
            end_time=time(16, 0),
            is_available=True
        )
        db.add(wh)
        working_hours_count += 1
    
    db.commit()
    print(f"✓ Created {working_hours_count} working hour slots")

def create_bookings(db: Session, users, barbers):
    """Create sample bookings"""
    print("Creating bookings...")
    
    # Get non-admin users for bookings
    customers = [u for u in users if not u.is_admin]
    
    bookings = [
        {
            "customer_id": customers[0].id,
            "barber_id": barbers[0].id,
            "booking_date": datetime.now() + timedelta(days=1, hours=10),
            "status": BookingStatus.CONFIRMED,
            "notes": "Пожалуйста, покороче по бокам"
        },
        {
            "customer_id": customers[1].id,
            "barber_id": barbers[1].id,
            "booking_date": datetime.now() + timedelta(days=2, hours=14),
            "status": BookingStatus.PENDING,
            "notes": None
        },
        {
            "customer_id": customers[2].id,
            "barber_id": barbers[2].id,
            "booking_date": datetime.now() + timedelta(days=3, hours=11),
            "status": BookingStatus.CONFIRMED,
            "notes": "Первый раз у вас"
        },
        {
            "customer_id": customers[0].id,
            "barber_id": barbers[0].id,
            "booking_date": datetime.now() - timedelta(days=5),
            "status": BookingStatus.COMPLETED,
            "notes": "Для сына"
        }
    ]
    
    db_bookings = []
    for booking_data in bookings:
        booking = Booking(**booking_data)
        db.add(booking)
        db_bookings.append(booking)
    
    db.commit()
    print(f"✓ Created {len(db_bookings)} bookings")
    return db_bookings

def seed_database():
    """Main function to seed the database"""
    print("\n🌱 Starting database seeding...\n")
    
    db = SessionLocal()
    
    try:
        # Clear existing data
        print("Clearing existing data...")
        db.query(Booking).delete()
        db.query(WorkingHours).delete()
        db.query(Barber).delete()
        db.query(User).delete()
        db.commit()
        print("✓ Cleared existing data\n")
        
        # Create data
        users = create_users(db)
        barbers = create_barbers(db)
        create_working_hours(db, barbers)
        create_bookings(db, users, barbers)
        
        print("\n✅ Database seeding completed successfully!\n")
        print("📝 Sample credentials:")
        print("   Admin (staff login): admin@barbershop.uz / admin123")
        print("   Customer (phone login): +998901111111 (John Doe)")
        print("   Customer (phone login): +998902222222 (Aziz Karimov)")
        print("   Customer (phone login): +998903333333 (Maria Koroleva)\n")
        
    except Exception as e:
        print(f"\n❌ Error seeding database: {e}")
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    seed_database()
from sqlalchemy.orm import Session
from app.database import SessionLocal, engine, Base
from app.models.user import User
from app.models.barber import Barber
from app.models.service import Service
from app.models.booking import Booking, BookingStatus
from app.models.working_hours import WorkingHours
from app.utils.security import get_password_hash
from datetime import datetime, time, timedelta
import json

def create_users(db: Session):
    """Create sample users"""
    print("Creating users...")
    
    users = [
        {
            "email": "admin@barbershop.uz",
            "username": "admin",
            "hashed_password": get_password_hash("admin123"),
            "full_name": "Admin User",
            "phone": "+998901234567",
            "is_active": True,
            "is_admin": True
        },
        {
            "email": "john@example.com",
            "username": "john_doe",
            "hashed_password": get_password_hash("password123"),
            "full_name": "John Doe",
            "phone": "+998901111111",
            "is_active": True,
            "is_admin": False
        },
        {
            "email": "aziz@example.com",
            "username": "aziz_uz",
            "hashed_password": get_password_hash("password123"),
            "full_name": "Aziz Karimov",
            "phone": "+998902222222",
            "is_active": True,
            "is_admin": False
        },
        {
            "email": "maria@example.com",
            "username": "maria_k",
            "hashed_password": get_password_hash("password123"),
            "full_name": "Maria Koroleva",
            "phone": "+998903333333",
            "is_active": True,
            "is_admin": False
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

def create_services(db: Session):
    """Create sample services"""
    print("Creating services...")
    
    services = [
        {
            "name": "Классическая стрижка",
            "description": "Традиционная мужская стрижка с укладкой",
            "price": 80000,  # 80,000 UZS
            "duration_minutes": 45,
            "is_active": True
        },
        {
            "name": "Стрижка + Борода",
            "description": "Комплекс: стрижка волос и оформление бороды",
            "price": 120000,  # 120,000 UZS
            "duration_minutes": 60,
            "is_active": True
        },
        {
            "name": "Бритье опасной бритвой",
            "description": "Традиционное бритье с горячим полотенцем",
            "price": 60000,  # 60,000 UZS
            "duration_minutes": 30,
            "is_active": True
        },
        {
            "name": "Детская стрижка",
            "description": "Стрижка для детей до 12 лет",
            "price": 50000,  # 50,000 UZS
            "duration_minutes": 30,
            "is_active": True
        }
    ]
    
    db_services = []
    for service_data in services:
        service = Service(**service_data)
        db.add(service)
        db_services.append(service)
    
    db.commit()
    print(f"✓ Created {len(db_services)} services")
    return db_services

def create_working_hours(db: Session, barbers):
    """Create working hours for barbers"""
    print("Creating working hours...")
    
    working_hours_count = 0
    for barber in barbers:
        # Monday to Friday: 9:00 - 18:00
        for day in range(5):  # 0-4 (Mon-Fri)
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

def create_bookings(db: Session, users, barbers, services):
    """Create sample bookings"""
    print("Creating bookings...")
    
    # Get non-admin users for bookings
    customers = [u for u in users if not u.is_admin]
    
    bookings = [
        {
            "customer_id": customers[0].id,
            "barber_id": barbers[0].id,
            "service_id": services[0].id,
            "booking_date": datetime.now() + timedelta(days=1, hours=10),
            "status": BookingStatus.CONFIRMED,
            "notes": "Пожалуйста, покороче по бокам"
        },
        {
            "customer_id": customers[1].id,
            "barber_id": barbers[1].id,
            "service_id": services[1].id,
            "booking_date": datetime.now() + timedelta(days=2, hours=14),
            "status": BookingStatus.PENDING,
            "notes": None
        },
        {
            "customer_id": customers[2].id,
            "barber_id": barbers[2].id,
            "service_id": services[2].id,
            "booking_date": datetime.now() + timedelta(days=3, hours=11),
            "status": BookingStatus.CONFIRMED,
            "notes": "Первый раз у вас"
        },
        {
            "customer_id": customers[0].id,
            "barber_id": barbers[0].id,
            "service_id": services[3].id,
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
        # Clear existing data (optional - comment out if you want to keep existing data)
        print("Clearing existing data...")
        db.query(Booking).delete()
        db.query(WorkingHours).delete()
        db.query(Service).delete()
        db.query(Barber).delete()
        db.query(User).delete()
        db.commit()
        print("✓ Cleared existing data\n")
        
        # Create data
        users = create_users(db)
        barbers = create_barbers(db)
        services = create_services(db)
        create_working_hours(db, barbers)
        create_bookings(db, users, barbers, services)
        
        print("\n✅ Database seeding completed successfully!\n")
        print("📝 Sample credentials:")
        print("   Admin: admin / admin123")
        print("   User:  john_doe / password123")
        print("   User:  aziz_uz / password123")
        print("   User:  maria_k / password123\n")
        
    except Exception as e:
        print(f"\n❌ Error seeding database: {e}")
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    seed_database()
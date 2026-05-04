from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.config import get_settings
from app.database import engine, Base
from app.routers import auth, users, barbers, bookings, barber_panel
from app.routers import ws as ws_router

settings = get_settings()

# Create database tables
Base.metadata.create_all(bind=engine)

app = FastAPI(
    title=settings.app_name,
    debug=settings.debug
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(auth.router)
app.include_router(users.router)
app.include_router(barbers.router)
app.include_router(bookings.router)
app.include_router(barber_panel.router)
app.include_router(ws_router.router)

@app.get("/")
async def root():
    return {"message": "Barber Shop Booking API", "status": "running"}

@app.get("/health")
async def health_check():
    return {"status": "healthy"}

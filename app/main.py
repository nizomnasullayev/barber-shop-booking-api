from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.config import get_settings
from app.database import engine, Base
from app.routers import auth, users, barbers, bookings, barber_panel, upload
from app.routers import ws as ws_router
import multiprocessing
from contextlib import asynccontextmanager
from app.telegram_bot import run_bot

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Start Telegram bot in a separate background process
    bot_process = multiprocessing.Process(target=run_bot, daemon=True)
    bot_process.start()
    
    yield
    
    # Shutdown bot when app stops
    bot_process.terminate()

settings = get_settings()

app = FastAPI(
    title=settings.app_name,
    debug=settings.debug,
    lifespan=lifespan
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "https://barber-shop-booking-app.vercel.app"
    ],
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
app.include_router(upload.router)

@app.get("/")
async def root():
    return {"message": "Barber Shop Booking API", "status": "running"}


@app.get("/health")
async def health_check():
    return {"status": "healthy"}
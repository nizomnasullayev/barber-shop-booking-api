import asyncio
from datetime import datetime
from telegram import Bot
from telegram.error import TelegramError
from app.config import get_settings
from app.utils.i18n import translate

settings = get_settings()

# Initialize bot
bot = Bot(token=settings.telegram_bot_token)


async def send_telegram_message(chat_id: str, message: str) -> bool:
    """
    Send a message via Telegram bot

    Args:
        chat_id: Telegram chat ID
        message: Message text to send

    Returns:
        True if sent successfully, False otherwise
    """
    try:
        await bot.send_message(
            chat_id=chat_id,
            text=message,
            parse_mode='HTML'
        )
        return True
    except TelegramError as e:
        print(f"Failed to send Telegram message: {e}")
        return False


def send_booking_confirmation(chat_id: str, customer_name: str, barber_name: str, booking_date: datetime, service: str, locale: str = 'ru'):
    """Send booking confirmation to user"""
    formatted_date = booking_date.strftime("%d.%m.%Y в %H:%M")

    message = translate(
        'bot.booking_confirmed_customer',
        locale=locale,
        name=customer_name,
        barber=barber_name,
        date=formatted_date,
        service=service or 'Стрижка'
    )
    asyncio.run(send_telegram_message(chat_id, message))


def send_booking_reminder(chat_id: str, customer_name: str, barber_name: str, booking_date: datetime):
    """Send booking reminder to user (24 hours before)"""
    formatted_date = booking_date.strftime("%d.%m.%Y в %H:%M")

    message = f"""
⏰ <b>Напоминание о записи!</b>

Здравствуйте, {customer_name}!

Завтра у вас запись к барберу {barber_name}
📅 Время: {formatted_date}

До встречи! 💈
"""
    asyncio.run(send_telegram_message(chat_id, message))


def send_barber_credentials(chat_id: str, name: str, email: str, password: str):
    """Send credentials to new barber"""
    message = f"""
👋 <b>Добро пожаловать, {name}!</b>

Вы были добавлены как барбер в систему Barber Shop.

📧 Email: <code>{email}</code>
🔑 Временный пароль: <code>{password}</code>

🌐 Войдите на сайт для управления записями:
https://barbershop.uz

⚠️ Рекомендуем сменить пароль после первого входа.
"""
    asyncio.run(send_telegram_message(chat_id, message))


def send_booking_cancelled(chat_id: str, customer_name: str, barber_name: str, booking_date: datetime):
    """Send cancellation notification"""
    formatted_date = booking_date.strftime("%d.%m.%Y в %H:%M")

    message = f"""
❌ <b>Запись отменена</b>

{customer_name}, ваша запись к барберу {barber_name} на {formatted_date} была отменена.

Вы можете записаться на другое время на нашем сайте.
"""
    asyncio.run(send_telegram_message(chat_id, message))


def send_booking_status_update(chat_id: str, customer_name: str, barber_name: str, booking_date: datetime, new_status: str, locale: str = 'ru'):
    """Send status update notification"""
    formatted_date = booking_date.strftime("%d.%m.%Y в %H:%M")

    # Map status to localized text
    status_map = {
        'confirmed': translate('booking.updated', locale=locale), # Or specific status word
        'pending': '...', 
        'cancelled': translate('booking.deleted', locale=locale),
        'completed': translate('general.success', locale=locale)
    }
    
    status_text = status_map.get(new_status, new_status)

    message = translate(
        'bot.status_update_customer',
        locale=locale,
        barber=barber_name,
        date=formatted_date,
        status=status_text
    )
    asyncio.run(send_telegram_message(chat_id, message))


def send_notification_to_barber(chat_id: str, customer_name: str, booking_date: datetime, notes: str, locale: str = 'ru'):
    """Send new booking notification to barber"""
    formatted_date = booking_date.strftime("%d.%m.%Y в %H:%M")

    message = translate(
        'bot.new_booking_barber',
        locale=locale,
        name=customer_name,
        date=formatted_date,
        notes=notes or '---'
    )
    asyncio.run(send_telegram_message(chat_id, message))


def send_cancellation_to_barber(chat_id: str, customer_name: str, booking_date: datetime, locale: str = 'ru'):
    """Notify barber that a customer has cancelled their booking"""
    formatted_date = booking_date.strftime("%d.%m.%Y в %H:%M")

    message = translate(
        'bot.booking_cancelled_barber',
        locale=locale,
        name=customer_name,
        date=formatted_date
    )
    asyncio.run(send_telegram_message(chat_id, message))

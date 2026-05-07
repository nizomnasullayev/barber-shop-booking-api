from app.config import get_settings
from app.database import SessionLocal
from app.models.user import User
from app.utils.i18n import translate
from telegram import Update, Bot, InlineKeyboardButton, InlineKeyboardMarkup, ReplyKeyboardMarkup, KeyboardButton
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes, CallbackQueryHandler

settings = get_settings()

# Initialize bot
bot = Bot(token=settings.telegram_bot_token)


async def get_user_locale(update: Update, context: ContextTypes.DEFAULT_TYPE) -> str:
    """Get user's preferred locale from context or DB"""
    if context and 'locale' in context.user_data:
        return context.user_data['locale']
    
    chat_id = update.effective_chat.id
    db = SessionLocal()
    try:
        user = db.query(User).filter(User.telegram_chat_id == str(chat_id)).first()
        if user and user.language:
            if context:
                context.user_data['locale'] = user.language
            return user.language
        return 'ru'
    finally:
        db.close()

async def get_main_keyboard(locale: str):
    """Generate the main reply keyboard based on locale"""
    # Fetch labels outside of f-string to avoid backslash issues
    help_label = translate('bot.help_btn', locale=locale) or ('Yordam' if locale == 'uz' else 'Справка')
    lang_label = translate('bot.lang_btn', locale=locale) or ('Til' if locale == 'uz' else 'Язык')
    link_label = translate('bot.link_btn', locale=locale) or ("Bog'lash" if locale == 'uz' else 'Привязать')
    
    buttons = [
        [
            KeyboardButton(f"📋 {help_label}"),
            KeyboardButton(f"🌐 {lang_label}")
        ],
        [
            KeyboardButton(f"🔗 {link_label}", request_contact=True)
        ]
    ]
    return ReplyKeyboardMarkup(buttons, resize_keyboard=True)

async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /start command"""
    locale = await get_user_locale(update, context)
    
    keyboard = await get_main_keyboard(locale)
    await update.message.reply_text(
        translate('bot.welcome', locale=locale),
        reply_markup=keyboard
    )

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle text messages from buttons"""
    text = update.message.text
    locale = await get_user_locale(update, context)

    # Help Button
    if "Yordam" in text or "Справка" in text or "/help" in text:
        await help_command(update, context)
    
    # Language Button
    elif "Til" in text or "Язык" in text or "/lang" in text:
        await lang_command(update, context)
    
    # Link Button
    elif "Bog'lash" in text or "Привязать" in text or "/link" in text:
        await start_command(update, context)
    
    # Otherwise treat as phone number for linking
    else:
        await handle_phone(update, context)

async def lang_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /lang command - show language selection"""
    locale = await get_user_locale(update, context)
    
    keyboard = [
        [
            InlineKeyboardButton("Русский 🇷🇺", callback_data='set_lang_ru'),
            InlineKeyboardButton("O'zbekcha 🇺🇿", callback_data='set_lang_uz')
        ]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await update.message.reply_text(
        translate('bot.select_language', locale=locale),
        reply_markup=reply_markup
    )

async def language_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle language selection callback"""
    query = update.callback_query
    await query.answer()
    
    new_lang = query.data.split('_')[-1]
    chat_id = update.effective_chat.id
    
    # Save to session
    context.user_data['locale'] = new_lang
    
    db = SessionLocal()
    try:
        user = db.query(User).filter(User.telegram_chat_id == str(chat_id)).first()
        if user:
            user.language = new_lang
            db.commit()
        
        await query.edit_message_text(translate('bot.lang_changed', locale=new_lang))
        
        # Update the main keyboard to the new language
        keyboard = await get_main_keyboard(new_lang)
        await query.message.reply_text(
            translate('bot.help', locale=new_lang),
            reply_markup=keyboard
        )
    finally:
        db.close()

async def handle_phone(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle phone number messages"""
    locale = await get_user_locale(update, context)
    phone = update.message.text.strip()

    if not phone.startswith('+') or len(phone) < 10:
        await update.message.reply_text(translate('bot.invalid_phone', locale=locale))
        return

    db = SessionLocal()
    try:
        user = db.query(User).filter(User.phone == phone).first()

        if not user:
            await update.message.reply_text(translate('bot.user_not_found', locale=locale))
            return

        user.telegram_chat_id = str(chat_id)
        # Inherit language from bot interaction if not set
        if not user.language:
            user.language = locale
        db.commit()

        await update.message.reply_text(
            translate('bot.link_success', locale=user.language, name=user.full_name, phone=user.phone)
        )
    except Exception as e:
        print(f"Error linking account: {e}")
        await update.message.reply_text("❌ Error / Ошибка / Xatolik")
    finally:
        db.close()

async def handle_contact(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle shared contact (phone number)"""
    locale = await get_user_locale(update, context)
    contact = update.message.contact
    
    # Ensure the phone number starts with +
    phone = contact.phone_number
    if not phone.startswith('+'):
        phone = f"+{phone}"

    db = SessionLocal()
    try:
        user = db.query(User).filter(User.phone == phone).first()

        if not user:
            await update.message.reply_text(translate('bot.user_not_found', locale=locale))
            return

        user.telegram_chat_id = str(chat_id)
        if not user.language:
            user.language = locale
        db.commit()

        await update.message.reply_text(
            translate('bot.link_success', locale=user.language, name=user.full_name, phone=user.phone)
        )
    except Exception as e:
        print(f"Error linking contact: {e}")
        await update.message.reply_text("❌ Error / Ошибка / Xatolik")
    finally:
        db.close()

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /help command"""
    locale = await get_user_locale(update, context)
    await update.message.reply_text(translate('bot.help', locale=locale))


async def link_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /link command - same as /start"""
    await start_command(update, context)


async def error_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle errors"""
    print(f"Update {update} caused error {context.error}")


def run_bot():
    """
    Run the Telegram bot
    This should be run in a separate thread/process
    """
    print("🤖 Starting Telegram bot...")

    # Create application
    application = Application.builder().token(settings.telegram_bot_token).build()

    # Add handlers
    application.add_handler(CommandHandler("start", start_command))
    application.add_handler(CommandHandler("help", help_command))
    application.add_handler(CommandHandler("lang", lang_command))
    application.add_handler(CommandHandler("link", link_command))
    application.add_handler(CallbackQueryHandler(language_callback, pattern='^set_lang_'))
    application.add_handler(MessageHandler(filters.CONTACT, handle_contact))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    # Add error handler
    application.add_error_handler(error_handler)

    # Run bot
    print("✅ Telegram bot is running...")
    application.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == "__main__":
    run_bot()

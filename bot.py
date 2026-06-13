import logging
from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes
from config import Config
from utils import setup_logging
from scheduler import SchedulerManager
from database import Database

logger = setup_logging()

async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = (
        "👋 Welcome to the FIFA World Cup 2026 Bot!\n\n"
        "I will automatically send match schedules, posters, and reminders to the configured channel.\n"
        f"Promo: {Config.PROMO_LINK}\n\n"
        "Use /help to see available commands."
    )
    await update.effective_chat.send_message(text, disable_web_page_preview=True)

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = (
        "🤖 <b>Available Commands:</b>\n"
        "/start - Welcome message\n"
        "/help - Show this message\n"
        "/today - Show today's fixtures\n"
        "/upcoming - Show upcoming fixtures\n"
    )
    await update.effective_chat.send_message(text, parse_mode='HTML')

async def today_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    db = Database()
    from datetime import datetime
    import pytz
    
    now = datetime.utcnow().replace(tzinfo=pytz.utc)
    start_of_day = now.strftime("%Y-%m-%dT00:00Z")
    end_of_day = now.strftime("%Y-%m-%dT23:59Z")
    
    fixtures = db.get_todays_fixtures(start_of_day, end_of_day)
    
    if not fixtures:
        await update.effective_chat.send_message("No matches scheduled for today.")
        return
        
    text = "📅 <b>Today's Matches</b> 📅\n\n"
    for i, match in enumerate(fixtures, 1):
        text += f"{i}️⃣ <b>{match['home_team_name']}</b> vs <b>{match['away_team_name']}</b>\n"
        text += f"   🕒 {match['date']}\n"
        
    await update.effective_chat.send_message(text, parse_mode='HTML')

async def upcoming_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    db = Database()
    fixtures = db.get_upcoming_fixtures()[:5] # Show next 5
    
    if not fixtures:
        await update.effective_chat.send_message("No upcoming matches found.")
        return
        
    text = "📅 <b>Next 5 Matches</b> 📅\n\n"
    for i, match in enumerate(fixtures, 1):
        text += f"{i}️⃣ <b>{match['home_team_name']}</b> vs <b>{match['away_team_name']}</b>\n"
        text += f"   🕒 {match['date']}\n"
        
    await update.effective_chat.send_message(text, parse_mode='HTML')

async def post_init(application: Application):
    logger.info("Initializing background tasks...")
    scheduler = SchedulerManager(application)
    scheduler.start()
    # Initial sync
    await scheduler.sync_fixtures()
    logger.info("Bot is ready to receive commands!")

def main():
    if not Config.BOT_TOKEN or Config.BOT_TOKEN == 'your_bot_token_here':
        logger.error("BOT_TOKEN is missing or invalid in .env")
        return

    application = Application.builder().token(Config.BOT_TOKEN).post_init(post_init).build()

    from telegram.ext import MessageHandler, filters
    import re
    
    # Commands using MessageHandler to catch them in channels as well
    application.add_handler(MessageHandler(filters.Regex(re.compile(r'^/start', re.IGNORECASE)), start_command))
    application.add_handler(MessageHandler(filters.Regex(re.compile(r'^/help', re.IGNORECASE)), help_command))
    application.add_handler(MessageHandler(filters.Regex(re.compile(r'^/today', re.IGNORECASE)), today_command))
    application.add_handler(MessageHandler(filters.Regex(re.compile(r'^/upcoming', re.IGNORECASE)), upcoming_command))

    # Start Bot
    logger.info("Bot is starting...")
    application.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == "__main__":
    main()

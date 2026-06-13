import html
from config import Config
from utils import setup_logging
from telegram.constants import ParseMode

logger = setup_logging()

class Notifier:
    def __init__(self, application):
        self.app = application
        self.channel_id = Config.CHANNEL_ID

    async def send_message(self, text, photo_path=None, chat_id=None):
        target_chat = chat_id or self.channel_id
        if not target_chat:
            logger.warning("No channel ID configured. Skipping notification.")
            return None

        try:
            if photo_path:
                with open(photo_path, 'rb') as photo:
                    msg = await self.app.bot.send_photo(
                        chat_id=target_chat,
                        photo=photo,
                        caption=text,
                        parse_mode=ParseMode.HTML
                    )
                    return msg.message_id
            else:
                msg = await self.app.bot.send_message(
                    chat_id=target_chat,
                    text=text,
                    parse_mode=ParseMode.HTML,
                    disable_web_page_preview=True
                )
                return msg.message_id
        except Exception as e:
            logger.error(f"Failed to send message to {target_chat}: {e}")
            return None

    async def update_match_result(self, message_id, match, chat_id=None):
        target_chat = chat_id or self.channel_id
        if not target_chat or not message_id:
            return
            
        home = html.escape(match['home_team_name'])
        away = html.escape(match['away_team_name'])
        stage = html.escape(match['stage'])
        
        text = (
            f"🏁 <b>FULL TIME</b> 🏁\n"
            f"<i>{stage}</i>\n\n"
            f"⚽ <b>{home}</b> {match['home_score']} - {match['away_score']} <b>{away}</b>\n\n"
            f"📅 <b>Date:</b> {match['date']} (UTC)\n"
        )
        
        try:
            await self.app.bot.edit_message_caption(
                chat_id=target_chat,
                message_id=int(message_id),
                caption=text,
                parse_mode=ParseMode.HTML
            )
            logger.info(f"Successfully updated match result for {match['match_id']}")
        except Exception as e:
            logger.error(f"Failed to edit message {message_id}: {e}")

    def format_match_reminder(self, match, time_label):
        """Formats a match reminder message."""
        home = html.escape(match['home_team_name'])
        away = html.escape(match['away_team_name'])
        venue = html.escape(match['venue'])
        stage = html.escape(match['stage'])
        
        # Parse date
        # Assuming date string is isoformat from DB, e.g. 2026-06-11T19:00Z
        # To keep things simple, we'll just print it as is, or you could parse to IST
        
        text = (
            f"🏆 <b>FIFA WORLD CUP 2026</b> 🏆\n"
            f"<i>{stage}</i>\n\n"
            f"⚽ <b>{home}</b> vs <b>{away}</b>\n"
            f"⏳ <b>Starts in:</b> {time_label}\n"
            f"🏟 <b>Venue:</b> {venue}\n"
            f"📅 <b>Kickoff:</b> {match['date']} (UTC)\n\n"
            f"🔗 <b>Follow Here:</b> {Config.PROMO_LINK}"
        )
        return text

    def format_daily_digest(self, fixtures):
        """Formats a summary of today's matches."""
        if not fixtures:
            return None
            
        text = "📅 <b>Today's FIFA World Cup Matches</b> 📅\n\n"
        for i, match in enumerate(fixtures, 1):
            home = html.escape(match['home_team_name'])
            away = html.escape(match['away_team_name'])
            text += f"{i}️⃣ <b>{home}</b> vs <b>{away}</b>\n"
            text += f"   🕒 {match['date']} (UTC)\n"
            
        text += f"\n🔗 <b>More info:</b> {Config.PROMO_LINK}"
        return text

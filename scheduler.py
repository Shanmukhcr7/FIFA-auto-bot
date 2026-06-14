from apscheduler.schedulers.asyncio import AsyncIOScheduler
from datetime import datetime, timedelta
import pytz
from database import Database
from espn_client import ESPNClient
from notifications import Notifier
from poster_generator import PosterGenerator
from utils import setup_logging, get_ist_time

logger = setup_logging()

class SchedulerManager:
    def __init__(self, application):
        self.scheduler = AsyncIOScheduler(timezone=pytz.timezone('Asia/Kolkata'))
        self.db = Database()
        self.espn = ESPNClient()
        self.notifier = Notifier(application)
        self.poster_gen = PosterGenerator()

    def start(self):
        # Job to sync fixtures every hour
        self.scheduler.add_job(self.sync_fixtures, 'interval', hours=1, id='sync_fixtures')
        
        # Job to check upcoming matches for reminders every minute
        self.scheduler.add_job(self.check_reminders, 'interval', minutes=1, id='check_reminders')
        
        # Job to send daily digest at 8 AM IST
        self.scheduler.add_job(self.send_daily_digest, 'cron', hour=8, minute=0, id='daily_digest')
        
        # Run an initial sync immediately on startup
        import asyncio
        asyncio.create_task(self.sync_fixtures())
        
        self.scheduler.start()
        logger.info("Scheduler started successfully.")

    async def sync_fixtures(self):
        logger.info("Syncing fixtures from ESPN...")
        now = datetime.utcnow()
        end_date = now + timedelta(days=7)
        # Fetch fixtures for the next 7 days to ensure we don't miss tomorrow's matches
        fixtures = self.espn.get_fixtures(
            start_date=now.strftime("%Y%m%d"),
            end_date=end_date.strftime("%Y%m%d")
        )
        if fixtures:
            self.db.update_fixtures(fixtures)
            logger.info(f"Successfully synced {len(fixtures)} fixtures.")

    async def check_reminders(self):
        upcoming = self.db.get_upcoming_fixtures()
        now = datetime.utcnow().replace(tzinfo=pytz.utc)
        
        # Prefetch the next 7 days of data once for all result checking
        latest_fixtures = []
        if any(minutes_passed >= 130 for match in upcoming for minutes_passed in [(now - datetime.strptime(match['date'], "%Y-%m-%dT%H:%MZ").replace(tzinfo=pytz.utc)).total_seconds() / 60.0 if not match.get('result_updated') and match.get('kickoff_message_id') else 0]):
            end_date = now + timedelta(days=7)
            latest_fixtures = self.espn.get_fixtures(
                start_date=(now - timedelta(days=2)).strftime("%Y%m%d"), # Look back 2 days for recently finished matches
                end_date=end_date.strftime("%Y%m%d")
            )
            
        for match in upcoming:
            # Parse kickoff time
            try:
                # Format from ESPN is typically: 2026-06-11T19:00Z
                kickoff = datetime.strptime(match['date'], "%Y-%m-%dT%H:%MZ").replace(tzinfo=pytz.utc)
            except ValueError:
                continue
                
            time_diff = now - kickoff
            minutes_passed = time_diff.total_seconds() / 60.0
            hours_diff = -time_diff.total_seconds() / 3600.0 # Negative means in the future
            
            # --- Check if match is finished (>= 130 minutes after kickoff) ---
            if minutes_passed >= 130 and match.get('kickoff_message_id') and not match.get('result_updated'):
                logger.info(f"Checking if match {match['match_id']} is finished...")
                for latest in latest_fixtures:
                    if latest['match_id'] == match['match_id']:
                        # ESPN uses STATUS_FULL_TIME for finished soccer matches
                        if latest['status'] in ['STATUS_FULL_TIME', 'STATUS_POSTPONED', 'STATUS_CANCELED']:
                            await self.notifier.update_match_result(match['kickoff_message_id'], latest)
                            self.db.set_result_updated(match['match_id'])
                        break
            
            # --- Scheduled Reminders ---
            # Map of notification labels to their time thresholds (in hours before kickoff)
            # User specifically requested ONLY sending at match start time
            reminders = {
                'kickoff': (-0.1, 0.1, "Kickoff!")
            }
            
            for r_type, (min_h, max_h, label) in reminders.items():
                if min_h <= hours_diff <= max_h:
                    if not self.db.is_notification_sent(match['match_id'], r_type):
                        logger.info(f"Sending {r_type} reminder for match {match['match_id']}")
                        
                        poster = self.poster_gen.generate_poster(match)
                        text = self.notifier.format_match_reminder(match, label)
                        
                        msg_id = await self.notifier.send_message(text, photo_path=poster)
                        self.db.mark_notification_sent(match['match_id'], r_type)
                        
                        if r_type == 'kickoff' and msg_id:
                            self.db.set_kickoff_message_id(match['match_id'], msg_id)

    async def send_daily_digest(self):
        logger.info("Sending daily digest...")
        now = datetime.utcnow().replace(tzinfo=pytz.utc)
        start_of_day = now.strftime("%Y-%m-%dT00:00Z")
        end_of_day = now.strftime("%Y-%m-%dT23:59Z")
        
        todays_fixtures = self.db.get_todays_fixtures(start_of_day, end_of_day)
        if todays_fixtures:
            text = self.notifier.format_daily_digest(todays_fixtures)
            if text:
                await self.notifier.send_message(text)

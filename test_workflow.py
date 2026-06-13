import asyncio
import os
from PIL import Image, ImageDraw
from config import Config
from telegram.ext import Application
from notifications import Notifier
import pytz
from datetime import datetime

# Helper to create a dummy image if none exists
def create_dummy_poster():
    os.makedirs(Config.POSTERS_DIR, exist_ok=True)
    path = os.path.join(Config.POSTERS_DIR, "test_poster.jpg")
    img = Image.new('RGB', (1080, 1350), color = (73, 109, 137))
    d = ImageDraw.Draw(img)
    d.text((400,600), "TEST MATCH POSTER", fill=(255,255,0))
    img.save(path)
    return path

async def main():
    print("[TEST] Starting the Full Process Test...")
    
    if not Config.BOT_TOKEN or Config.BOT_TOKEN == 'your_bot_token_here':
        print("[ERROR] BOT_TOKEN is missing from .env!")
        return
    if not Config.CHANNEL_ID or Config.CHANNEL_ID == 'your_channel_id_here':
        print("[ERROR] CHANNEL_ID is missing from .env!")
        return

    # Initialize Bot Application
    app = Application.builder().token(Config.BOT_TOKEN).build()
    await app.initialize()
    
    notifier = Notifier(app)
    
    # Create Dummy Match Data
    now_utc = datetime.utcnow().strftime("%Y-%m-%dT%H:%MZ")
    dummy_match = {
        'match_id': 'test_123',
        'home_team_name': 'Brazil',
        'away_team_name': 'Argentina',
        'home_score': '2',
        'away_score': '1',
        'stage': 'Final',
        'venue': 'Test Stadium',
        'date': now_utc
    }
    
    poster_path = create_dummy_poster()
    
    print("\n[Step 1] Sending the Kickoff Notification to the Channel...")
    kickoff_text = notifier.format_match_reminder(dummy_match, "Kickoff!")
    
    msg_id = await notifier.send_message(kickoff_text, photo_path=poster_path)
    
    if not msg_id:
        print("[ERROR] Failed to send message. Please check your BOT_TOKEN and CHANNEL_ID.")
        return
        
    print(f"[SUCCESS] Kickoff message sent! (Message ID: {msg_id})")
    print("[WAIT] Waiting 10 seconds to simulate 100 minutes of match time...")
    
    await asyncio.sleep(10)
    
    print("\n[Step 2] Match finished! Updating the message with the final result...")
    await notifier.update_match_result(msg_id, dummy_match)
    
    print("[SUCCESS] Message successfully updated. Check your Telegram channel to see the final result without the promo link!")

if __name__ == "__main__":
    import sys
    sys.stdout.reconfigure(encoding='utf-8')
    asyncio.run(main())

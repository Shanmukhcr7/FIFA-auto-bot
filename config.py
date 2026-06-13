import os
from dotenv import load_dotenv

# Load environment variables from .env file if it exists
load_dotenv()

class Config:
    BOT_TOKEN = os.getenv('BOT_TOKEN')
    CHANNEL_ID = os.getenv('CHANNEL_ID')
    TIMEZONE = os.getenv('TIMEZONE', 'Asia/Kolkata')
    
    # ESPN API Configuration
    ESPN_BASE_URL = 'https://site.api.espn.com/apis/site/v2/sports/soccer/fifa.world'
    ESPN_STANDINGS_URL = 'https://site.api.espn.com/apis/v2/sports/soccer/fifa.world'
    
    # Paths
    BASE_DIR = os.path.dirname(os.path.abspath(__file__))
    DB_PATH = os.path.join(BASE_DIR, 'data', 'fixtures.db')
    ASSETS_DIR = os.path.join(BASE_DIR, 'assets')
    FLAGS_DIR = os.path.join(ASSETS_DIR, 'flags')
    POSTERS_DIR = os.path.join(ASSETS_DIR, 'posters')
    BACKGROUNDS_DIR = os.path.join(ASSETS_DIR, 'backgrounds')
    
    # Links
    PROMO_LINK = "https://fifa-world-cup-2026-pearl.vercel.app/"

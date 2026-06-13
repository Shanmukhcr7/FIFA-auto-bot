import logging
from logging.handlers import RotatingFileHandler
import os
import pytz
from datetime import datetime

def setup_logging():
    os.makedirs('logs', exist_ok=True)
    
    logger = logging.getLogger('fifa_bot')
    logger.setLevel(logging.INFO)
    
    if not logger.handlers:
        # File handler
        file_handler = RotatingFileHandler(
            'logs/bot.log', 
            maxBytes=5*1024*1024, # 5 MB
            backupCount=3
        )
        file_formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        file_handler.setFormatter(file_formatter)
        logger.addHandler(file_handler)
        
        # Console handler
        console_handler = logging.StreamHandler()
        console_handler.setFormatter(file_formatter)
        logger.addHandler(console_handler)
        
    return logger

def get_ist_time(dt=None):
    if dt is None:
        dt = datetime.utcnow()
    elif dt.tzinfo is None:
        dt = pytz.utc.localize(dt)
        
    ist = pytz.timezone('Asia/Kolkata')
    return dt.astimezone(ist)

def format_date(dt):
    return dt.strftime('%A, %d %b %Y')

def format_time(dt):
    return dt.strftime('%I:%M %p %Z')

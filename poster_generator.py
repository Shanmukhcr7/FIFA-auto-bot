import os
import requests
from PIL import Image, ImageDraw, ImageFont, ImageFilter
from io import BytesIO
from config import Config
from utils import setup_logging

logger = setup_logging()

class PosterGenerator:
    def __init__(self):
        os.makedirs(Config.FLAGS_DIR, exist_ok=True)
        os.makedirs(Config.POSTERS_DIR, exist_ok=True)
        os.makedirs(Config.BACKGROUNDS_DIR, exist_ok=True)
        
        self.width = 1080
        self.height = 1350
        
    def _download_image(self, url, filepath):
        if os.path.exists(filepath):
            return True
        try:
            r = requests.get(url, stream=True, timeout=10)
            if r.status_code == 200:
                with open(filepath, 'wb') as f:
                    for chunk in r.iter_content(1024):
                        f.write(chunk)
                return True
        except Exception as e:
            logger.error(f"Error downloading image {url}: {e}")
        return False

    def _get_flag(self, team_id, logo_url):
        if not logo_url:
            return None
        ext = logo_url.split('.')[-1].split('?')[0]
        if not ext or len(ext) > 4:
            ext = 'png'
        filepath = os.path.join(Config.FLAGS_DIR, f"{team_id}.{ext}")
        if self._download_image(logo_url, filepath):
            return filepath
        return None

    def _create_background(self):
        bg_path = os.path.join(Config.BACKGROUNDS_DIR, "default.jpg")
        if os.path.exists(bg_path):
            return Image.open(bg_path).convert("RGBA")
        
        # Create a default dark gradient background if none exists
        img = Image.new("RGBA", (self.width, self.height), "#1a1a2e")
        draw = ImageDraw.Draw(img)
        for y in range(self.height):
            r = int(26 + (y / self.height) * 20)
            g = int(26 + (y / self.height) * 20)
            b = int(46 + (y / self.height) * 30)
            draw.line([(0, y), (self.width, y)], fill=(r, g, b, 255))
        return img

    def generate_poster(self, match):
        """Generates a poster for the match and returns the file path."""
        match_id = match['match_id']
        poster_path = os.path.join(Config.POSTERS_DIR, f"match_{match_id}.jpg")
        
        if os.path.exists(poster_path):
            return poster_path
            
        try:
            bg = self._create_background()
            draw = ImageDraw.Draw(bg)
            
            # Download flags
            home_flag_path = self._get_flag(match['home_team_id'], match['home_team_logo'])
            away_flag_path = self._get_flag(match['away_team_id'], match['away_team_logo'])
            
            # Load and paste flags
            flag_size = (300, 300)
            if home_flag_path and os.path.exists(home_flag_path):
                try:
                    home_img = Image.open(home_flag_path).convert("RGBA").resize(flag_size)
                    bg.paste(home_img, (150, 400), home_img)
                except Exception as e:
                    logger.error(f"Error processing home flag: {e}")
                    
            if away_flag_path and os.path.exists(away_flag_path):
                try:
                    away_img = Image.open(away_flag_path).convert("RGBA").resize(flag_size)
                    bg.paste(away_img, (630, 400), away_img)
                except Exception as e:
                    logger.error(f"Error processing away flag: {e}")
            
            # Add "VS" text
            try:
                font_vs = ImageFont.truetype("arial.ttf", 100)
                font_title = ImageFont.truetype("arial.ttf", 60)
                font_subtitle = ImageFont.truetype("arial.ttf", 40)
            except:
                font_vs = ImageFont.load_default()
                font_title = ImageFont.load_default()
                font_subtitle = ImageFont.load_default()
            
            draw.text((self.width//2, 550), "VS", font=font_vs, fill="white", anchor="mm")
            
            # Team Names
            draw.text((300, 750), match['home_team_name'][:15], font=font_title, fill="white", anchor="mm")
            draw.text((780, 750), match['away_team_name'][:15], font=font_title, fill="white", anchor="mm")
            
            # Header
            draw.text((self.width//2, 150), "FIFA WORLD CUP 2026", font=font_title, fill="#FFD700", anchor="mm")
            draw.text((self.width//2, 250), match['stage'].upper(), font=font_subtitle, fill="white", anchor="mm")
            
            # Match Info
            draw.text((self.width//2, 950), f"Venue: {match['venue']}", font=font_subtitle, fill="#CCCCCC", anchor="mm")
            draw.text((self.width//2, 1050), f"Promo: {Config.PROMO_LINK}", font=font_subtitle, fill="#00FF00", anchor="mm")
            
            bg = bg.convert("RGB")
            bg.save(poster_path, quality=90)
            return poster_path
            
        except Exception as e:
            logger.error(f"Failed to generate poster for {match_id}: {e}")
            return None

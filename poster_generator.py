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
        
        # Local bundled fonts
        self.font_bold_path = os.path.join(Config.ASSETS_DIR, "Roboto-Bold.ttf")
        self.font_regular_path = os.path.join(Config.ASSETS_DIR, "Roboto-Regular.ttf")

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
        bg_path = os.path.join(Config.BACKGROUNDS_DIR, "stadium.png")
        if os.path.exists(bg_path):
            img = Image.open(bg_path).convert("RGBA")
            # Resize to ensure it perfectly matches the canvas size
            return img.resize((self.width, self.height), Image.Resampling.LANCZOS)
        
        # Fallback if image is missing
        img = Image.new("RGBA", (self.width, self.height), "#0B0E14")
        return img

    def _add_drop_shadow(self, img, offset=(10, 10), radius=15, color=(0,0,0,150)):
        # Pad the image so the shadow doesn't get clipped
        padding = radius * 2
        padded_size = (img.size[0] + padding*2, img.size[1] + padding*2)
        
        background = Image.new("RGBA", padded_size, (0,0,0,0))
        shadow = Image.new("RGBA", padded_size, (0,0,0,0))
        
        # Create shadow mask
        shadow.paste(color, (padding + offset[0], padding + offset[1]), mask=img)
        shadow = shadow.filter(ImageFilter.GaussianBlur(radius))
        
        # Paste shadow then original image
        background.paste(shadow, (0,0), shadow)
        background.paste(img, (padding, padding), img)
        return background

    def generate_poster(self, match):
        """Generates an aesthetic poster for the match."""
        match_id = match['match_id']
        poster_path = os.path.join(Config.POSTERS_DIR, f"match_{match_id}.jpg")
        
        try:
            bg = self._create_background()
            draw = ImageDraw.Draw(bg)
            
            # Load Fonts
            try:
                font_super = ImageFont.truetype(self.font_bold_path, 120)
                font_title = ImageFont.truetype(self.font_bold_path, 80)
                font_subtitle = ImageFont.truetype(self.font_regular_path, 45)
                font_small = ImageFont.truetype(self.font_regular_path, 35)
            except:
                font_super = font_title = font_subtitle = font_small = ImageFont.load_default()
            
            # Header
            draw.text((self.width//2, 100), "FIFA WORLD CUP 2026", font=font_title, fill="#E6C861", anchor="mm")
            draw.text((self.width//2, 180), match['stage'].upper(), font=font_subtitle, fill="#A0AEC0", anchor="mm")
            
            # Flags Setup
            home_flag_path = self._get_flag(match['home_team_id'], match['home_team_logo'])
            away_flag_path = self._get_flag(match['away_team_id'], match['away_team_logo'])
            
            flag_max_size = (350, 240)
            flag_y = 600
            
            if home_flag_path and os.path.exists(home_flag_path):
                try:
                    home_img = Image.open(home_flag_path).convert("RGBA")
                    home_img.thumbnail(flag_max_size, Image.Resampling.LANCZOS)
                    home_img = self._add_drop_shadow(home_img)
                    w, h = home_img.size
                    bg.paste(home_img, (270 - w//2, flag_y - h//2), home_img)
                except Exception as e:
                    logger.error(f"Error processing home flag: {e}")
                    
            if away_flag_path and os.path.exists(away_flag_path):
                try:
                    away_img = Image.open(away_flag_path).convert("RGBA")
                    away_img.thumbnail(flag_max_size, Image.Resampling.LANCZOS)
                    away_img = self._add_drop_shadow(away_img)
                    w, h = away_img.size
                    bg.paste(away_img, (810 - w//2, flag_y - h//2), away_img)
                except Exception as e:
                    logger.error(f"Error processing away flag: {e}")
            
            # "VS" Center Text
            draw.text((self.width//2, flag_y), "VS", font=font_super, fill="#FFFFFF", anchor="mm")
            
            # Team Names
            draw.text((270, flag_y + 180), match['home_team_name'].upper()[:15], font=font_title, fill="#FFFFFF", anchor="mm")
            draw.text((810, flag_y + 180), match['away_team_name'].upper()[:15], font=font_title, fill="#FFFFFF", anchor="mm")
            
            bg = bg.convert("RGB")
            bg.save(poster_path, quality=95)
            return poster_path
            
        except Exception as e:
            logger.error(f"Failed to generate poster for {match_id}: {e}")
            return None

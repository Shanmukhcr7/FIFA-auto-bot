import requests
import json
from config import Config
from utils import setup_logging
from datetime import datetime

logger = setup_logging()

class ESPNClient:
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'
        })

    def get_fixtures(self, start_date=None, end_date=None):
        """
        Fetch fixtures for FIFA World Cup from ESPN.
        Optionally filter by dates (YYYYMMDD).
        """
        url = f"{Config.ESPN_BASE_URL}/scoreboard"
        params = {}
        if start_date and end_date:
            params['dates'] = f"{start_date}-{end_date}"
            
        try:
            response = self.session.get(url, params=params, timeout=10)
            response.raise_for_status()
            data = response.json()
            return self._parse_fixtures(data)
        except Exception as e:
            logger.error(f"Failed to fetch fixtures: {e}")
            return []

    def _parse_fixtures(self, data):
        parsed = []
        events = data.get('events', [])
        for event in events:
            match_id = event.get('id')
            date = event.get('date') # ISO format: 2026-06-11T19:00Z
            name = event.get('name')
            status = event.get('status', {}).get('type', {}).get('name', 'UNKNOWN')
            
            competitions = event.get('competitions', [])
            if not competitions:
                continue
                
            comp = competitions[0]
            venue = comp.get('venue', {}).get('fullName', 'Unknown Venue')
            
            # Usually two competitors: Home and Away
            competitors = comp.get('competitors', [])
            home_team = {}
            away_team = {}
            
            for c in competitors:
                team_data = {
                    'id': c.get('team', {}).get('id'),
                    'name': c.get('team', {}).get('displayName'),
                    'abbr': c.get('team', {}).get('abbreviation'),
                    'logo': c.get('team', {}).get('logo'),
                    'score': c.get('score', '0')
                }
                if c.get('homeAway') == 'home':
                    home_team = team_data
                else:
                    away_team = team_data
                    
            # Fallback if home/away not explicitly set (rare)
            if not home_team and len(competitors) >= 1:
                home_team = {'id': competitors[0].get('team', {}).get('id'), 'name': competitors[0].get('team', {}).get('displayName'), 'abbr': competitors[0].get('team', {}).get('abbreviation'), 'logo': competitors[0].get('team', {}).get('logo'), 'score': competitors[0].get('score', '0')}
            if not away_team and len(competitors) >= 2:
                away_team = {'id': competitors[1].get('team', {}).get('id'), 'name': competitors[1].get('team', {}).get('displayName'), 'abbr': competitors[1].get('team', {}).get('abbreviation'), 'logo': competitors[1].get('team', {}).get('logo'), 'score': competitors[1].get('score', '0')}

            stage = "Group Stage" # Example stage, could be parsed if available
            
            parsed.append({
                'match_id': match_id,
                'date': date,
                'status': status,
                'home_team_id': home_team.get('id'),
                'home_team_name': home_team.get('name'),
                'home_team_abbr': home_team.get('abbr'),
                'home_team_logo': home_team.get('logo'),
                'home_score': home_team.get('score'),
                'away_team_id': away_team.get('id'),
                'away_team_name': away_team.get('name'),
                'away_team_abbr': away_team.get('abbr'),
                'away_team_logo': away_team.get('logo'),
                'away_score': away_team.get('score'),
                'venue': venue,
                'stage': stage
            })
            
        return parsed

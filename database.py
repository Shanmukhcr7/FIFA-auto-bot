import sqlite3
import os
import json
from config import Config
from utils import setup_logging

logger = setup_logging()

class Database:
    def __init__(self, db_path=Config.DB_PATH):
        self.db_path = db_path
        self._init_db()

    def get_connection(self):
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn

    def _init_db(self):
        os.makedirs(os.path.dirname(self.db_path), exist_ok=True)
        with self.get_connection() as conn:
            cursor = conn.cursor()
            
            # Fixtures table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS fixtures (
                    match_id TEXT PRIMARY KEY,
                    date TEXT NOT NULL,
                    status TEXT,
                    home_team_id TEXT,
                    home_team_name TEXT,
                    home_team_abbr TEXT,
                    home_team_logo TEXT,
                    home_score TEXT,
                    away_team_id TEXT,
                    away_team_name TEXT,
                    away_team_abbr TEXT,
                    away_team_logo TEXT,
                    away_score TEXT,
                    venue TEXT,
                    stage TEXT,
                    kickoff_message_id TEXT,
                    result_updated INTEGER DEFAULT 0
                )
            ''')
            # Add columns if they don't exist (for seamless upgrade)
            try:
                cursor.execute("ALTER TABLE fixtures ADD COLUMN kickoff_message_id TEXT")
                cursor.execute("ALTER TABLE fixtures ADD COLUMN result_updated INTEGER DEFAULT 0")
            except sqlite3.OperationalError:
                pass # Columns already exist
            
            # Notifications table to track what we've sent
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS notifications (
                    match_id TEXT,
                    notification_type TEXT,
                    sent_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    PRIMARY KEY (match_id, notification_type)
                )
            ''')
            
            conn.commit()

    def update_fixtures(self, fixtures):
        """Insert or update a list of fixtures."""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            for f in fixtures:
                cursor.execute('''
                    INSERT INTO fixtures (
                        match_id, date, status, 
                        home_team_id, home_team_name, home_team_abbr, home_team_logo, home_score,
                        away_team_id, away_team_name, away_team_abbr, away_team_logo, away_score,
                        venue, stage
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    ON CONFLICT(match_id) DO UPDATE SET
                        date=excluded.date,
                        status=excluded.status,
                        home_score=excluded.home_score,
                        away_score=excluded.away_score,
                        venue=excluded.venue,
                        stage=excluded.stage
                ''', (
                    f['match_id'], f['date'], f['status'],
                    f['home_team_id'], f['home_team_name'], f['home_team_abbr'], f['home_team_logo'], f['home_score'],
                    f['away_team_id'], f['away_team_name'], f['away_team_abbr'], f['away_team_logo'], f['away_score'],
                    f['venue'], f['stage']
                ))
            conn.commit()

    def set_kickoff_message_id(self, match_id, message_id):
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('UPDATE fixtures SET kickoff_message_id = ? WHERE match_id = ?', (message_id, match_id))
            conn.commit()

    def set_result_updated(self, match_id):
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('UPDATE fixtures SET result_updated = 1 WHERE match_id = ?', (match_id,))
            conn.commit()

    def get_upcoming_fixtures(self):
        """Get fixtures that haven't finished, plus fixtures that finished but haven't updated results."""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                SELECT * FROM fixtures 
                WHERE (status NOT IN ('STATUS_FINAL', 'STATUS_POSTPONED', 'STATUS_CANCELED') 
                       OR result_updated = 0)
                ORDER BY date ASC
            ''')
            return [dict(row) for row in cursor.fetchall()]

    def is_notification_sent(self, match_id, notification_type):
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                SELECT 1 FROM notifications 
                WHERE match_id = ? AND notification_type = ?
            ''', (match_id, notification_type))
            return cursor.fetchone() is not None

    def mark_notification_sent(self, match_id, notification_type):
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                INSERT OR IGNORE INTO notifications (match_id, notification_type) 
                VALUES (?, ?)
            ''', (match_id, notification_type))
            conn.commit()
            
    def get_todays_fixtures(self, start_of_day, end_of_day):
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                SELECT * FROM fixtures 
                WHERE date >= ? AND date <= ?
                ORDER BY date ASC
            ''', (start_of_day, end_of_day))
            return [dict(row) for row in cursor.fetchall()]

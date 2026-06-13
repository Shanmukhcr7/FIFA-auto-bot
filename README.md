# FIFA World Cup 2026 Telegram Bot

A production-ready Telegram bot that automatically publishes FIFA World Cup 2026 match schedules, generated posters, and reminders to your Telegram channel. Data is sourced from the ESPN API.

## Features
- **Automated Sync**: Fetches live fixture data directly from ESPN API.
- **Match Posters**: Automatically generates aesthetic posters for upcoming matches using Pillow.
- **Smart Reminders**: Sends scheduled notifications to your channel at 24h, 12h, 1h, and Kickoff times.
- **Daily Digest**: Sends a summary of today's matches every morning at 8:00 AM IST.
- **Promo Link**: Appends your custom website link to all notifications.

## Requirements
- Python 3.12+
- A Telegram Bot Token from [@BotFather](https://t.me/botfather)
- The target Telegram Channel ID

## Local Setup (Windows / Ubuntu / Termux)

1. **Clone/Setup the repository**:
   Navigate to the project directory.

2. **Install Dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

3. **Configure Environment Variables**:
   Copy the example environment file and fill in your details:
   ```bash
   cp .env.example .env
   ```
   Edit `.env` and set `BOT_TOKEN` and `CHANNEL_ID`.
   Make sure your bot is added as an Administrator to your Telegram Channel.

4. **Run the Bot**:
   ```bash
   python bot.py
   ```

## Docker Deployment

1. **Build and Run**:
   Ensure Docker and Docker Compose are installed, and your `.env` file is ready.
   ```bash
   docker-compose up -d
   ```

2. **View Logs**:
   ```bash
   docker-compose logs -f
   ```

## Deploying on a VPS (Systemd Service)

To keep the bot running 24/7 on an Ubuntu VPS without Docker:

1. Create a service file:
   ```bash
   sudo nano /etc/systemd/system/fifabot.service
   ```

2. Add the following (adjust paths to match your setup):
   ```ini
   [Unit]
   Description=FIFA 2026 Bot
   After=network.target

   [Service]
   User=root
   WorkingDirectory=/path/to/fifa_bot
   ExecStart=/usr/bin/python3 /path/to/fifa_bot/bot.py
   Restart=always

   [Install]
   WantedBy=multi-user.target
   ```

3. Enable and start:
   ```bash
   sudo systemctl daemon-reload
   sudo systemctl enable fifabot
   sudo systemctl start fifabot
   ```

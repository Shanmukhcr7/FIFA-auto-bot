import os
import requests
from dotenv import load_dotenv

load_dotenv()

TOKEN = os.getenv("BOT_TOKEN")

if not TOKEN:
    print("No token found.")
    exit()

print("Fetching latest messages sent to the bot...")
try:
    response = requests.get(f"https://api.telegram.org/bot{TOKEN}/getUpdates")
    data = response.json()
    
    if not data.get("ok"):
        print("Error fetching updates:", data)
    else:
        results = data.get("result", [])
        if not results:
            print("No messages found! Make sure you have added the bot to your channel/group and sent a message recently.")
        else:
            for update in results:
                if "channel_post" in update:
                    chat = update["channel_post"]["chat"]
                    print(f"FOUND CHANNEL! Name: {chat.get('title')}, Chat ID: {chat.get('id')}")
                elif "message" in update:
                    chat = update["message"]["chat"]
                    chat_type = chat.get('type')
                    name = chat.get('title') or chat.get('first_name') or chat.get('username')
                    print(f"FOUND {chat_type.upper()}! Name: {name}, Chat ID: {chat.get('id')}")
                    
except Exception as e:
    print(f"Request failed: {e}")

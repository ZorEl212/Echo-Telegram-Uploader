#!/usr/bin/env python3

from pyrogram import Client, filters
import os
import time
import sys
from tqdm import tqdm
import configparser

# Read configuration from config.ini
config = configparser.ConfigParser()
data_dir = os.path.join(os.getenv("HOME"), ".tup")
config.read(os.path.join(data_dir, "config.ini"))

API_ID = config.get('telegram', 'api_id')
API_HASH = config.get('telegram', 'api_hash')
BOT_TOKEN = config.get('telegram', 'bot_token')
SESSION_PATH = data_dir
GROUP_CHAT_ID = config.get('telegram', 'group_chat_id')

# Create a Pyrogram client
app = Client(os.path.join(SESSION_PATH,"my_bot"),
             api_id=API_ID,
             api_hash=API_HASH,
             bot_token=BOT_TOKEN)

async def send_global_message(client, file_path):
    file_size = os.path.getsize(file_path)
    with tqdm(total=file_size, unit='B', unit_scale=True, unit_divisor=1024) as pbar:
        async def progress(current, total):
            pbar.update(current - pbar.n)

        try:
            await client.send_document(GROUP_CHAT_ID, file_path, progress=progress)
        except Exception as e:
            print(f"Failed to send file to the group chat: {str(e)}")

if __name__ == "__main__":
    filename = sys.argv[2] if len(sys.argv) > 2 and sys.argv[1] == "-f" else None
    if filename:
        async def main():
            async with app:
                await send_global_message(app, filename)
        app.run(main())
    else:
        print("Usage: python tup.py -f <file_path>")
        sys.exit(1)

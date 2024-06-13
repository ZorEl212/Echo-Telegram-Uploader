#!/usr/bin/env python3

from pyrogram import Client, filters
import os
import time
import sys
from tqdm import tqdm

# Your bot token
API_ID = os.getenv("API_ID") if os.getenv("API_ID") else input("Enter API ID: ")
API_HASH = os.getenv("API_HASH") if os.getenv("API_HASH") else input("Enter API HASH: ")
BOT_TOKEN = os.getenv("BOT_TOKEN") if os.getenv("BOT_TOKEN") else input("Enter BOT TOKEN: ")

# Group chat ID
GROUP_CHAT_ID = os.getenv("GROUP_CHAT_ID") if os.getenv("GROUP_CHAT_ID") else input("Enter GROUP CHAT ID: ")

# Create a Pyrogram client
app = Client("my_bot", api_id=API_ID, api_hash=API_HASH, bot_token=BOT_TOKEN)

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

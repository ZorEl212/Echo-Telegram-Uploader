#!/usr/bin/env python3

from pyrogram import Client, filters
import os
import time
import sys

# Your bot token
API_ID = os.getenv("API_ID", input("Enter API ID: "))
API_HASH = os.getenv("API_HASH", input("Enter API HASH: "))
BOT_TOKEN = os.getenv("BOT_TOKEN",  input("Enter BOT TOKEN: "))
SESSION_PATH = os.getenv("SESSION_PATH", "./")
GROUP_CHAT_ID = os.getenv("GROUP_CHAT_ID",  input("Enter GROUP CHAT ID: "))

# Create a Pyrogram client
app = Client(os.path.join(SESSION_PATH, "my_bot"),
              api_id=API_ID,
                api_hash=API_HASH, 
                bot_token=BOT_TOKEN)

@app.on_message(filters.command("start"))
async def start(client, message):
    await message.reply_text("Welcome! Use /upload <file_path> to upload a file.")

@app.on_message(filters.command("upload"))
async def upload_file(client, message):
    if str(message.chat.type) not in ["ChatType.SUPERGROUP", "ChatType.GROUP"]:
        await message.reply_text("Oops! this command can only be used in groups!")
        return

    try:
        file_path = message.text.split(" ", maxsplit=1)[1]
        filename = os.path.basename(file_path)
    except IndexError:
        await message.reply_text("Please provide a file path.")
        return

    if not os.path.exists(file_path):
        await message.reply_text("File not found.")
        return

    progress_message = await message.reply_text("Starting to upload file...")
    last_update_time = time.time()
    update_interval = 5  # seconds
    last_percentage = 0
    percentage_update_threshold = 10  # update every 10%

    # Keep track of the progress while uploading
    async def progress(current, total):
        percent = current / total * 100
        nonlocal last_update_time, last_percentage
        current_time = time.time()
        if percent - last_percentage > percentage_update_threshold or current_time - last_update_time > update_interval:
            await progress_message.edit_text(f"Uploaded {percent:.1f}%")
            last_update_time = current_time
            last_percentage = percent

    try:
        await client.send_document(message.chat.id, file_path, progress=progress)
        await progress_message.edit_text("Upload finished.")
    except Exception as e:
        await progress_message.edit_text(f"An error occurred: {str(e)}")


if __name__ == "__main__":
        app.run()

#!/usr/bin/env python3

from pyrogram import Client, filters
import os
import time
import sys
import json
from models import config, storage
from collections import defaultdict
from pyrogram.types import (
    ReplyKeyboardMarkup, InlineKeyboardMarkup, InlineKeyboardButton)

data_dir = os.path.join(os.getenv("HOME"), ".echo")
API_ID = config.get('API_ID')
API_HASH = config.get('API_HASH')
BOT_TOKEN = config.get('BOT_TOKEN')
SESSION_PATH = data_dir
GROUP_CHAT_ID = config.get('GROUP_CHAT_ID')

# Create a Pyrogram client
bot = Client(os.path.join(SESSION_PATH, "my_bot"),
              api_id=API_ID,
              api_hash=API_HASH, 
              bot_token=BOT_TOKEN)
build_reports = {}  # Store build reports with IDs

def listen_to_redis():
    pubsub = config.pubsub()
    pubsub.subscribe("build_reports")
    for message in pubsub.listen():
        if message['type'] == 'message':
            data = json.loads(message['data'])
            build_id = data.get('build_id')
            build_reports[build_id] = data  # Store or update the report

@bot.on_message(filters.command("start"))
async def start(client, message):
    await message.reply_text("Welcome! Use /upload <file_path> to upload a file.")

@bot.on_message(filters.command("id"))
async def get_chat_id(client, message):
    await message.reply_text(f"Chat ID: {message.chat.id}")

@bot.on_message(filters.command("button"))
async def button(client, message):
    await bot.send_message(
    message.chat.id, "These are inline buttons",
    reply_markup=InlineKeyboardMarkup(
        [
            [InlineKeyboardButton("Servers", callback_data="get_servers")],
            [InlineKeyboardButton("Docs", url="https://docs.pyrogram.org")]
        ]))

@bot.on_callback_query()
async def handle_callback_query(client, callback_query):
    if callback_query.data == "data_button":
        await callback_query.answer("You pressed the Data button!")
        # You can perform any action here, like sending a message back to the user
        await bot.send_message(
            chat_id=callback_query.message.chat.id,
            text="Here’s the data you requested!"
        )
    if callback_query.data == "get_servers":
        user = storage.get_by_attr('User', 'telegram_id', str(callback_query.message.chat.id))
        if user:
            servers = storage.all('Server', 'userId', user.id)
            if servers:
                server_names = {server['id']: server['serverName'] for server in servers.values()}
                reply_markup = InlineKeyboardMarkup([
                    [InlineKeyboardButton(name, callback_data=_id)] for _id, name in server_names.items()
                ])
                await callback_query.message.edit("Available Servers:",
                                       reply_markup=reply_markup)
            else:
                await bot.send_message(callback_query.message.chat.id, "Sorry no servers are availablle for this user!")
        else:
            await bot.send_message(callback_query.message.chat.id, "Sorry you're not registered!")

@bot.on_message(filters.command("upload"))
async def upload_file(client, message):
    if str(message.chat.type) not in ["ChatType.SUPERGROUP", "ChatType.GROUP"]:
        await message.reply_text("Oops! this command can only be used in groups!")
        return

    if message.chat.id != int(GROUP_CHAT_ID):
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
    bot.run()
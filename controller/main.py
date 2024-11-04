#!/usr/bin/env python3

from pyrogram import filters
from pyromod import Client, Message
import os
import time
import asyncio
from models.user import User
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

bot = Client(os.path.join(SESSION_PATH, "my_bot"),
              api_id=API_ID,
              api_hash=API_HASH, 
              bot_token=BOT_TOKEN)

running_updates = {}
def query_servers(userId):
    servers = storage.all('Server', 'userId', userId) or storage.all('Server', 'users', userId)
    if servers:
        return {server['id']: server['serverName'] for server in servers.values()}

@bot.on_message(filters.command("start"))
async def start(client, message):
    await message.reply_text("Welcome! Use /menu to get started.")

@bot.on_message(filters.command("id"))
async def get_chat_id(client, message):
    user = storage.get_by_attr(User, 'telegram_id', str(message.chat.id))
    if user:
        await message.reply_text(f"Registered ID: `{user.id}`")
        return
    await message.reply_text(f"You're not registered yet.")

@bot.on_message(filters.command("menu"))
async def button(client, message):
    await bot.send_message(
    message.chat.id, "Options:",
    reply_markup=InlineKeyboardMarkup(
        [
            [InlineKeyboardButton("Register", callback_data="register")],
            [InlineKeyboardButton("Add user to server", callback_data="add_user")],
            [InlineKeyboardButton("Builds", callback_data="get_builds")]
        ]))

@bot.on_callback_query()
async def handle_callback_query(client, callback_query):
    global running_updates
    if callback_query.data == "register":
        user = storage.get_by_attr(User, 'telegram_id', str(callback_query.message.chat.id))
        if user:
            await bot.send_message(
                chat_id=callback_query.message.chat.id,
                text="You're already registered, use /id to view your ID"
            )
            return

        user = User(
            telegram_id=str(callback_query.message.chat.id),
            tgUsername=str(callback_query.message.chat.username),
            fullName=str(callback_query.message.chat.first_name) + " " + str(callback_query.message.chat.last_name)
        )
        storage.new(user)

        await bot.send_message(
            chat_id=callback_query.message.chat.id,
            text=f"Registered successfully!\nName: {user.fullName} \nID: `{user.id}`",
            reply_markup=InlineKeyboardMarkup(
                [[InlineKeyboardButton("Back to Menu", callback_data="back_to_menu")]]
            )
        )

    elif callback_query.data == "add_user":
        user = storage.get_by_attr(User, 'telegram_id', str(callback_query.message.chat.id))
        if user:
            server_names = query_servers(user.id)
            if server_names:
                # Create a list of buttons with a prefix to identify server callbacks
                reply_markup = InlineKeyboardMarkup([
                    [InlineKeyboardButton(name, callback_data=f"server_{_id}")] for _id, name in server_names.items()
                ] + [[InlineKeyboardButton("Back to Menu", callback_data="back_to_menu")]])  # Add back button
                await callback_query.message.edit(
                    "Available Servers:",
                    reply_markup=reply_markup
                )
            else:
                await bot.send_message(
                    chat_id=callback_query.message.chat.id,
                    text="Sorry, no servers are available for this user!",
                    reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("Back to Menu", callback_data="back_to_menu")]])
                )

    elif callback_query.data.startswith("server_"):
        server_id = callback_query.data.split("_", 1)[1]
        server = storage.get('Server', server_id)
        user = storage.get_by_attr(User, 'telegram_id', str(callback_query.message.chat.id))
        if user.id != server.userId:
            await callback_query.message.reply_text("You're not admin of the server!",
                reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("Back", callback_data="add_user")]]))
        else:
            chat = callback_query.message.chat
            user_id = await chat.ask("Enter user ID", filters=filters.text)
            if storage.get(User, user_id.text):
                server.add_user(user_id.text)
                await callback_query.message.reply("User added to server.")
            else:
                await callback_query.message.reply("User doesn't exist!")

    elif callback_query.data == "get_builds":
        user = storage.get_by_attr('User', 'telegram_id', str(callback_query.message.chat.id))
        if user:
            server_names = query_servers(user.id)
            if server_names:
                reply_markup = InlineKeyboardMarkup([
                    [InlineKeyboardButton(name, callback_data=f"sBuilds_{_id}")] for _id, name in server_names.items()
                ] + [[InlineKeyboardButton("Back to Menu", callback_data="back_to_menu")]])
                await callback_query.message.edit("Available Servers:", reply_markup=reply_markup)
            else:
                await bot.send_message(callback_query.message.chat.id, "Sorry no servers are available for this user!",
                                       reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("Back to Menu", callback_data="back_to_menu")]]))
        else:
            await bot.send_message(callback_query.message.chat.id, "Sorry you're not registered yet!",
                                   reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("Back to Menu", callback_data="back_to_menu")]]))
    elif callback_query.data.startswith("sBuilds_"):
        user = storage.get_by_attr('User', 'telegram_id', str(callback_query.message.chat.id))
        server_id = callback_query.data.split("_", 1)[1]
        server = storage.get('Server', server_id)
        builds = storage.all('Build', 'serverId', server_id)
        filtered_builds = {k: v for k, v in builds.items() if user.id == v['userId']}
        if len(filtered_builds) > 0:
            reply_markup = InlineKeyboardMarkup([
                [InlineKeyboardButton(name['buildName'], callback_data=f"Builds_{name['id']}")] for name in filtered_builds.values()
            ] + [[InlineKeyboardButton("Back", callback_data="get_builds")]])
            await callback_query.message.edit('Available builds:', reply_markup=reply_markup)
        else:
            await callback_query.message.reply("You have no builds on this server.",
                                               reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("Back", callback_data="get_builds")]]))

    elif callback_query.data.startswith("Builds_"):
        reply_markup = InlineKeyboardMarkup([
                [InlineKeyboardButton("Back", callback_data='stop_and_back')]
            ])
        build_id = callback_query.data.split("_", 1)[1]
        build = storage.get('Build', build_id)
            # Set up a flag for running updates
        running_updates[callback_query.message.chat.id] = True

        try:
            while running_updates[callback_query.message.chat.id]:
                if build.report.get('status', None) == 'success':
                    await callback_query.message.reply('Build completed successfully')
                    break
                elif build.report.get('status', None) == 'failed':
                    await callback_query.message.edit('Build failed.\n Error Log: ')
                    break
                else:
                    report = f"""
                    Progress: {build.report.get('progress')}/100
                    Tasks done: {build.report.get('tasks_done')}
                    Total Tasks: {build.report.get('total_tasks')}
                    Description: {build.report.get('description')}
                    """
                    await callback_query.message.edit(report, reply_markup=reply_markup)
                    await asyncio.sleep(5)  # Wait before checking again
                    build = storage.get('Build', build_id)

        finally:
            # Clean up after the loop
            if callback_query.message.chat.id in running_updates:
                del running_updates[callback_query.message.chat.id]

    elif callback_query.data == "stop_and_back":
        running_updates[callback_query.message.chat.id] = False
        callback_query.data = "get_builds"
        await handle_callback_query(client, callback_query)
    elif callback_query.data == "back_to_menu":
        await button(client, callback_query.message)  # Go back to the main menu

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
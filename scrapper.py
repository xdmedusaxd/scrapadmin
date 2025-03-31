import re
import asyncio
import json
from pyrogram import Client, filters, enums
from pyrogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton
from datetime import datetime
import os
import config

# Create Clients
bot = Client("bot", api_id=config.API_ID, api_hash=config.API_HASH, bot_token=config.BOT_TOKEN)
user = Client("user", api_id=config.API_ID, api_hash=config.API_HASH, session_string=config.SESSION_STRING)

# Create temp directory if not exists
if not os.path.exists("temp"):
    os.makedirs("temp")

# Function to check if user is admin
def is_admin(user_id):
    return user_id in config.ADMIN_IDS

# Function to check if user is approved
def is_approved(user_id):
    return user_id in config.APPROVED_USERS or user_id in config.ADMIN_IDS

# Function to save updated user lists to .env file
def save_users_to_env():
    # Read current .env file content
    with open('.env', 'r') as f:
        env_lines = f.readlines()

    # Update or add ADMIN_IDS and APPROVED_USERS
    admin_line_found = False
    approved_line_found = False

    for i, line in enumerate(env_lines):
        if line.startswith('ADMIN_IDS='):
            env_lines[i] = f'ADMIN_IDS={",".join(map(str, config.ADMIN_IDS))}\n'
            admin_line_found = True
        elif line.startswith('APPROVED_USERS='):
            # Convert to JSON string
            json_str = json.dumps(config.APPROVED_USERS)
            env_lines[i] = f'APPROVED_USERS={json_str}\n'
            approved_line_found = True

    if not admin_line_found:
        env_lines.append(f'ADMIN_IDS={",".join(map(str, config.ADMIN_IDS))}\n')
    if not approved_line_found:
        # Convert to JSON string
        json_str = json.dumps(config.APPROVED_USERS)
        env_lines.append(f'APPROVED_USERS={json_str}\n')

    # Write back to .env file
    with open('.env', 'w') as f:
        f.writelines(env_lines)

# Start command
@bot.on_message(filters.command("start") & filters.private)
async def start_command(client, message):
    user_id = message.from_user.id
    if not is_approved(user_id) and not is_admin(user_id):
        await message.reply("You are not authorized to use this bot. Please contact an admin for approval.")
        return

    text = """
Welcome to Card Scrapper Bot 🤖
Use /scr command to grab cards

**Syntax:** `/scr channel amount prefix`

**Example:** 
`/scr @channel 1000 401658`
`/scr @channel 1000`

**Optional:** 
- Prefix: To filter cards with a specific prefix
"""
    await message.reply(text)

# Help command
@bot.on_message(filters.command(["help"]) & filters.private)
async def help_command(client, message):
    user_id = message.from_user.id
    if not is_approved(user_id) and not is_admin(user_id):
        await message.reply("You are not authorized to use this bot. Please contact an admin for approval.")
        return

    if is_admin(user_id):
        text = """
**Admin Commands:**
`/adduser [user_id] [name]` - Add a user to approved users list
`/removeuser [user_id]` - Remove a user from approved users list
`/addadmin [user_id]` - Promote a user to admin
`/removeadmin [user_id]` - Demote an admin to regular user
`/listusers` - List all approved users
`/listadmins` - List all admins

**Scraper Commands:**
`/scr [channel] [amount] [prefix]` - Scrape cards from a channel
`/src [channel] [amount] [prefix]` - Alternate scraper command
"""
    else:
        text = """
**Scraper Commands:**
`/scr [channel] [amount] [prefix]` - Scrape cards from a channel
`/src [channel] [amount] [prefix]` - Alternate scraper command

Examples:
`/scr @channel 1000 401658`
`/scr @channel 1000`
"""
    await message.reply(text)

# Add approved user command
@bot.on_message(filters.command("adduser") & filters.private)
async def add_user_command(client, message):
    user_id = message.from_user.id
    if not is_admin(user_id):
        await message.reply("You are not authorized to use this command.")
        return

    # Extract user ID and name to add
    try:
        parts = message.text.split(" ", 2)
        if len(parts) < 3:
            await message.reply("Invalid format. Use `/adduser [user_id] [name]`")
            return

        user_to_add = int(parts[1])
        name = parts[2]

        if user_to_add in config.APPROVED_USERS:
            await message.reply(f"User {user_to_add} is already approved. Updating name.")

        config.APPROVED_USERS[user_to_add] = name
        save_users_to_env()
        await message.reply(f"User {user_to_add} ({name}) has been approved to use the bot.")
    except (IndexError, ValueError):
        await message.reply("Invalid format. Use `/adduser [user_id] [name]`")

# Remove approved user command
@bot.on_message(filters.command("removeuser") & filters.private)
async def remove_user_command(client, message):
    user_id = message.from_user.id
    if not is_admin(user_id):
        await message.reply("You are not authorized to use this command.")
        return

    # Extract user ID to remove
    try:
        user_to_remove = int(message.text.split()[1])
        if user_to_remove not in config.APPROVED_USERS:
            await message.reply(f"User {user_to_remove} is not in the approved list.")
            return

        name = config.APPROVED_USERS.pop(user_to_remove)
        save_users_to_env()
        await message.reply(f"User {user_to_remove} ({name}) has been removed from approved users.")
    except (IndexError, ValueError):
        await message.reply("Invalid format. Use `/removeuser [user_id]`")

# Add admin command
@bot.on_message(filters.command("addadmin") & filters.private)
async def add_admin_command(client, message):
    user_id = message.from_user.id
    if not is_admin(user_id):
        await message.reply("You are not authorized to use this command.")
        return

    # Extract user ID to add as admin
    try:
        new_admin = int(message.text.split()[1])
        if new_admin in config.ADMIN_IDS:
            await message.reply(f"User {new_admin} is already an admin.")
            return

        config.ADMIN_IDS.append(new_admin)
        save_users_to_env()

        # Get name if the user is in approved users
        name = config.APPROVED_USERS.get(new_admin, "Unknown")
        await message.reply(f"User {new_admin} ({name}) has been promoted to admin.")
    except (IndexError, ValueError):
        await message.reply("Invalid format. Use `/addadmin [user_id]`")

# Remove admin command
@bot.on_message(filters.command("removeadmin") & filters.private)
async def remove_admin_command(client, message):
    user_id = message.from_user.id
    if not is_admin(user_id):
        await message.reply("You are not authorized to use this command.")
        return

    # Extract user ID to remove as admin
    try:
        admin_to_remove = int(message.text.split()[1])
        if admin_to_remove not in config.ADMIN_IDS:
            await message.reply(f"User {admin_to_remove} is not an admin.")
            return

        config.ADMIN_IDS.remove(admin_to_remove)
        save_users_to_env()

        # Get name if the user is in approved users
        name = config.APPROVED_USERS.get(admin_to_remove, "Unknown")
        await message.reply(f"User {admin_to_remove} ({name}) has been removed from admins.")
    except (IndexError, ValueError):
        await message.reply("Invalid format. Use `/removeadmin [user_id]`")

# List approved users command
@bot.on_message(filters.command("listusers") & filters.private)
async def list_users_command(client, message):
    user_id = message.from_user.id
    if not is_admin(user_id):
        await message.reply("You are not authorized to use this command.")
        return

    if not config.APPROVED_USERS:
        await message.reply("No approved users found.")
        return

    users_list = "**Approved Users:**\n"
    for i, (uid, name) in enumerate(config.APPROVED_USERS.items(), 1):
        users_list += f"{i}. {uid} - {name}\n"

    await message.reply(users_list)

# List admins command
@bot.on_message(filters.command("listadmins") & filters.private)
async def list_admins_command(client, message):
    user_id = message.from_user.id
    if not is_admin(user_id):
        await message.reply("You are not authorized to use this command.")
        return

    if not config.ADMIN_IDS:
        await message.reply("No admins found.")
        return

    admins_list = "**Admin Users:**\n"
    for i, admin_id in enumerate(config.ADMIN_IDS, 1):
        # Get name if the admin is in approved users
        name = config.APPROVED_USERS.get(admin_id, "Unknown")
        admins_list += f"{i}. {admin_id} - {name}\n"

    await message.reply(admins_list)

# Scrape command
@bot.on_message(filters.command(["scr", "src"]) & filters.private)
async def scrape_command(client, message):
    user_id = message.from_user.id
    if not is_approved(user_id) and not is_admin(user_id):
        await message.reply("You are not authorized to use this bot. Please contact an admin for approval.")
        return

    cmd = message.text.split()
    if len(cmd) < 3:
        await message.reply(
            "Invalid format. Use `/scr channel amount [prefix]`\n\nExample:\n"
            "`/scr @channel 1000 401658`\n"
            "`/scr @channel 1000`"
        )
        return

    channel = cmd[1]
    try:
        amount = min(int(cmd[2]), config.MAX_MESSAGES)
    except ValueError:
        await message.reply("Amount must be a number")
        return

    prefix = cmd[3] if len(cmd) > 3 else None

    msg = await message.reply("Scraping in progress...")

    try:
        cards = await get_cards(channel, amount, prefix, msg)
        if len(cards) == 0:
            await msg.edit("No cards found matching your criteria")
            return

        now = datetime.now().strftime("%Y%m%d_%H%M%S")
        file_path = f"temp/cards_{now}.txt"
        with open(file_path, "w") as f:
            f.write("\n".join(cards))

        await msg.edit("Scraping completed. Sending results...")

        caption = f"📤 **Scraping Results**\n\n"                 f"• **Source:** {channel}\n"                 f"• **Messages Scraped:** {amount}\n"                 f"• **Cards Found:** {len(cards)}\n"                 f"• **Prefix Filter:** {prefix if prefix else 'None'}\n"

        await bot.send_document(
            chat_id=message.chat.id,
            document=file_path,
            caption=caption
        )
        os.remove(file_path)
    except Exception as e:
        await msg.edit(f"Error: {str(e)}")

# Card pattern regex
card_pattern = re.compile(r"(\d{16}|\d{4}\s\d{4}\s\d{4}\s\d{4})")

# Function to grab cards from channel
async def get_cards(channel, amount, prefix=None, status_msg=None):
    cards = []
    count = 0
    status_update_interval = max(1, min(amount // 10, 50))  # Update status every 10% or 50 messages, whichever is less

    try:
        async for message in user.get_chat_history(channel, limit=amount):
            count += 1

            if count % status_update_interval == 0:
                progress = (count / amount) * 100
                await status_msg.edit(f"Scraping: {count}/{amount} messages ({progress:.1f}%)")

            if message.text:
                matches = card_pattern.findall(message.text)
                if matches:
                    for card in matches:
                        card = card.replace(" ", "")  # Remove spaces
                        if prefix and not card.startswith(prefix):
                            continue
                        cards.append(card)

        # Remove duplicates while preserving order
        unique_cards = []
        seen = set()
        for card in cards:
            if card not in seen:
                unique_cards.append(card)
                seen.add(card)

        return unique_cards
    except Exception as e:
        raise Exception(f"Failed to scrape: {str(e)}")

# Run both clients
async def main():
    await bot.start()
    await user.start()
    print("Bot started!")
    await asyncio.Future()  # Keep running

if __name__ == "__main__":
    asyncio.run(main())

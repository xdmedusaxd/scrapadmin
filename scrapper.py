import re
import asyncio
import json
from pyrogram import Client, filters
from pyrogram.types import Message
from datetime import datetime
import os
import config

# Create Clients with proper parameters to prevent SESSION_REVOKED
bot = Client("bot", api_id=config.API_ID, api_hash=config.API_HASH, bot_token=config.BOT_TOKEN)
user = Client(
    "user_session", 
    api_id=config.API_ID, 
    api_hash=config.API_HASH, 
    session_string=config.SESSION_STRING,
    workers=1000,  # Reduced from 1000 to a more reasonable number
    no_updates=True  # This prevents the SESSION_REVOKED error
)

# Create temp directory if not exists
if not os.path.exists(config.TEMP_DIR):
    os.makedirs(config.TEMP_DIR)

# Function to check if user is admin
def is_admin(user_id):
    return user_id in config.ADMIN_IDS

# Function to check if user is approved
def is_approved(user_id):
    return user_id in config.APPROVED_USERS or user_id in config.ADMIN_IDS

# Function to save updated user lists to storage
def save_users_to_storage():
    """Save users to a data file for persistence on Render"""
    data = {
        'ADMIN_IDS': config.ADMIN_IDS,
        'APPROVED_USERS': config.APPROVED_USERS
    }
    
    # Ensure directory exists
    os.makedirs(os.path.dirname(config.DATA_FILE), exist_ok=True)
    
    with open(config.DATA_FILE, 'w') as f:
        json.dump(data, f)
    
    print(f"User data saved to {config.DATA_FILE}")

# Function to load users from storage
def load_users_from_storage():
    """Load users from the data file if it exists"""
    try:
        if os.path.exists(config.DATA_FILE):
            with open(config.DATA_FILE, 'r') as f:
                data = json.load(f)
                config.ADMIN_IDS = data.get('ADMIN_IDS', config.ADMIN_IDS)
                config.APPROVED_USERS = {int(k): v for k, v in data.get('APPROVED_USERS', {}).items()}
            print(f"User data loaded from {config.DATA_FILE}")
            print(f"Admins: {len(config.ADMIN_IDS)}, Approved Users: {len(config.APPROVED_USERS)}")
    except Exception as e:
        print(f"Error loading user data: {e}")

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
        save_users_to_storage()
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
        save_users_to_storage()
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
        save_users_to_storage()
        
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
        save_users_to_storage()
        
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
        file_path = f"{config.TEMP_DIR}/cards_{now}.txt"
        with open(file_path, "w") as f:
            f.write("\n".join(cards))
        
        await msg.edit("Scraping completed. Sending results...")
        
        caption = f"📤 **Scraping Results**\n\n" \
                 f"• **Source:** {channel}\n" \
                 f"• **Messages Scraped:** {amount}\n" \
                 f"• **Cards Found:** {len(cards)}\n" \
                 f"• **Prefix Filter:** {prefix if prefix else 'None'}\n"
        
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
        # Safer approach with error handling
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
        except Exception as e:
            await status_msg.edit(f"Error during scraping: {str(e)}\nRetrieved {count} messages before error.")
        
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

# Run both clients with error handling
async def main():
    try:
        # Load saved users data
        load_users_from_storage()
        
        # Start the bot client
        await bot.start()
        print("Bot started successfully!")
        
        try:
            # Try to start the user client with extra error handling
            await user.start()
            print(f"User client started successfully!")
        except Exception as e:
            print(f"Failed to start user client: {str(e)}")
            print("Bot will continue running, but scraping functionality will be limited.")
        
        print(f"Bot Username: @{(await bot.get_me()).username}")
        await asyncio.Future()  # Keep running
    except Exception as e:
        print(f"Critical error in main: {str(e)}")
        raise  # Re-raise the exception to exit with error

if __name__ == "__main__":
    asyncio.run(main())

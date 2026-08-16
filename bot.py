import os
import asyncio
import discord
from discord.ext import commands, tasks

# 1. Define Intents
intents = discord.Intents.default()
intents.members = True          # Required for on_member_join
intents.message_content = True  # Required for reading commands

# 2. Initialize Bot
bot = commands.Bot(command_prefix="!", intents=intents)

# 3. Dynamic Discord Presence / Activity Task
@tasks.loop(seconds=7)
async def change_status():
    activities = [
        discord.Activity(type=discord.ActivityType.watching, name="ishq™ Community"),
        discord.Activity(type=discord.ActivityType.listening, name="!help | ishq™"),
        discord.Game(name="Welcome to ishq™")
    ]
    for activity in activities:
        await bot.change_presence(activity=activity, status=discord.Status.online)
        await asyncio.sleep(60)  # Switch presence every 60 seconds

@bot.event
async def on_ready():
    print("=" * 50)
    print(f"Logged in as: {bot.user.name} (ID: {bot.user.id})")
    print("Main file: bot.py initialized successfully.")
    print("Loading commands from 'commands/' directory...")
    print("=" * 50)

    # Start presence rotation loop
    if not change_status.is_running():
        change_status.start()

# 4. Async function to load all cogs/commands from the commands/ folder
async def load_extensions():
    for filename in os.listdir("./commands"):
        if filename.endswith(".py"):
            await bot.load_extension(f"commands.{filename[:-3]}")
            print(f"[Loaded Extension]: commands/{filename}")

# 5. Main Execution Block
async def main():
    async with bot:
        await load_extensions()
        
        # Retrieves token from host environment variables
        token = os.getenv("DISCORD_TOKEN")
        
        if not token:
            print("ERROR: 'DISCORD_TOKEN' environment variable is missing!")
            print("Please set 'DISCORD_TOKEN' in your hosting environment variables.")
            return

        await bot.start(token)

if __name__ == "__main__":
    asyncio.run(main())
  

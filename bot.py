import os
import discord
from discord.ext import commands
from dotenv import load_dotenv

# Load environment variables
load_dotenv()
TOKEN = os.getenv('DISCORD_TOKEN')
PREFIX = os.getenv('DISCORD_PREFIX', '/')
MP3_FOLDER = os.getenv('MP3_FOLDER', './quran_mp3s')

intents = discord.Intents.default()
intents.message_content = True

bot = commands.Bot(command_prefix=PREFIX, intents=intents)

# Ensure MP3 folder exists and has files
if not os.path.exists(MP3_FOLDER):
    os.makedirs(MP3_FOLDER)
    print(f"Created MP3 folder at {MP3_FOLDER}")

mp3_files = [f for f in os.listdir(MP3_FOLDER) if f.endswith('.mp3')]
if not mp3_files:
    print(f"WARNING: No MP3 files found in {MP3_FOLDER}!")
else:
    print(f"Found {len(mp3_files)} MP3 files in {MP3_FOLDER}")

async def load_cogs():
    for filename in os.listdir('./cogs'):
        if filename.endswith('.py'):
            await bot.load_extension(f'cogs.{filename[:-3]}')

async def register_commands():
    # Register global commands
    await bot.tree.sync()
    print("Commands synced!")

@bot.event
async def on_ready():
    print(f'Logged in as {bot.user.name}')
    await bot.change_presence(activity=discord.Activity(
        type=discord.ActivityType.listening,
        name="the Quran"
    ))
    await register_commands()

async def main():
    await load_cogs()
    await bot.start(TOKEN)

if __name__ == '__main__':
    import asyncio
    asyncio.run(main()) 
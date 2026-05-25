import os
import asyncio
import discord
from discord.ext import commands
from macros import PREFIX
from dotenv import load_dotenv

load_dotenv()
BOT_TOKEN = os.getenv("DISCORD_TOKEN")
if not BOT_TOKEN:
    raise KeyError("Discord Token Key not found")

intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix=PREFIX, intents=intents, help_command=None)

queues = {}
voice_clients = {}

async def load():
    for filename in os.listdir('./cogs'):
        if filename.endswith('.py'):
            await bot.load_extension(f'cogs.{filename[:-3]}')

async def main():
    await load()
    print("Commands loaded.")
    await bot.start(token=BOT_TOKEN)

if __name__ == "__main__":
    asyncio.run(main())
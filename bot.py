import discord
from discord.ext import commands
import os

intents = discord.Intents.default()
intents.message_content = True

bot = commands.Bot(command_prefix="!", intents=intents)

@bot.event
async def on_ready():
    print(f"Logged in as {bot.user}")
    try:
        await bot.load_extension("cogs.status")
        print("Status cog loaded")
    except Exception as e:
        print(e)

bot.run(os.getenv("TOKEN"))

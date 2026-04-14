import discord
from discord.ext import commands
import os

# 🔧 CONFIG
GUILD_ID = 1493552564799672320

# 🔥 Intents
intents = discord.Intents.default()
intents.message_content = True
intents.members = True

bot = commands.Bot(command_prefix="!", intents=intents)


# 🚀 LOAD COGS + SYNC COMMANDS
@bot.event
async def setup_hook():
    print("⚙️ Loading cogs...")

    for file in os.listdir("./cogs"):
        if file.endswith(".py"):
            try:
                await bot.load_extension(f"cogs.{file[:-3]}")
                print(f"✅ Loaded cog: {file}")
            except Exception as e:
                print(f"❌ Failed to load {file}: {e}")

    # ⚡ Instant sync to your server
    guild = discord.Object(id=GUILD_ID)
    synced = await bot.tree.sync(guild=guild)
    print(f"⚡ Synced {len(synced)} command(s)")


@bot.event
async def on_ready():
    print(f"✅ Logged in as {bot.user}")


# ▶️ RUN BOT
TOKEN = os.getenv("TOKEN")

if not TOKEN:
    print("❌ TOKEN not found!")
else:
    bot.run(TOKEN)

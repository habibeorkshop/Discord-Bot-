import discord
from discord.ext import commands
import os

# 🔥 Intents
intents = discord.Intents.default()
intents.message_content = True
intents.members = True

bot = commands.Bot(command_prefix="!", intents=intents)


# ✅ LOAD COGS + SYNC (BEST METHOD)
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

    # 🔥 Sync slash commands
    try:
        synced = await bot.tree.sync()
        print(f"🌐 Synced {len(synced)} slash command(s)")
    except Exception as e:
        print(f"❌ Sync error: {e}")


@bot.event
async def on_ready():
    print(f"✅ Logged in as {bot.user}")


@bot.event
async def on_connect():
    print("🔄 Bot connected...")


# ▶️ Run bot
TOKEN = os.getenv("TOKEN")

if not TOKEN:
    print("❌ TOKEN not found! Add it in Railway variables.")
else:
    bot.run(TOKEN)

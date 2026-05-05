import discord
from discord.ext import commands
import os

# 🔧 CONFIG
GUILD_ID = 1493552564799672320  # your server ID

# 🔥 Intents
intents = discord.Intents.default()
intents.message_content = True
intents.members = True

bot = commands.Bot(command_prefix="!", intents=intents)


# 🚀 READY EVENT
@bot.event
async def on_ready():
    print(f"✅ Logged in as {bot.user}")

    # 🔌 LOAD COGS
    print("⚙️ Loading cogs...")
    for file in os.listdir("./cogs"):
        if file.endswith(".py"):
            try:
                await bot.load_extension(f"cogs.{file[:-3]}")
                print(f"✅ Loaded cog: {file}")
            except Exception as e:
                print(f"❌ Failed to load {file}: {e}")

    # ⚡ FORCE GUILD SYNC (INSTANT COMMANDS)
    try:
        guild = discord.Object(id=GUILD_ID)

        bot.tree.copy_global_to(guild=guild)
        synced = await bot.tree.sync(guild=guild)

        print(f"⚡ Synced {len(synced)} command(s) to guild")
    except Exception as e:
        print(f"❌ Sync error: {e}")


# 🔄 DEBUG CONNECT
@bot.event
async def on_connect():
    print("🔄 Bot connected...")


# 🧪 OPTIONAL: DEBUG COMMAND
@bot.tree.command(name="test", description="Test command")
async def test(interaction: discord.Interaction):
    await interaction.response.send_message("✅ Slash commands working!")


# ▶️ RUN
TOKEN = os.getenv("TOKEN")

if not TOKEN:
    print("❌ TOKEN not found! Add it in Railway variables.")
else:
    bot.run(TOKEN)

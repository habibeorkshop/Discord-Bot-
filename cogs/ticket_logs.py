import discord
from discord.ext import commands
import datetime
import os

# 🔧 CONFIG
LOG_CHANNEL_ID = 1493921223770378291


class TicketLogs(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    # 📜 CREATE TRANSCRIPT
    async def create_transcript(self, channel: discord.TextChannel):

        messages = []

        async for msg in channel.history(limit=None, oldest_first=True):
            time = msg.created_at.strftime("%Y-%m-%d %H:%M")
            content = msg.content if msg.content else ""
            messages.append(f"[{time}] {msg.author}: {content}")

        file_name = f"transcript-{channel.name}.txt"

        with open(file_name, "w", encoding="utf-8") as f:
            f.write("\n".join(messages))

        return file_name

    # 📊 LOG CLOSE
    async def log_close(self, interaction: discord.Interaction):

        log_channel = interaction.guild.get_channel(LOG_CHANNEL_ID)

        if log_channel:
            await log_channel.send(
                f"🔒 Ticket closed: {interaction.channel.name} by {interaction.user.mention}"
            )

    # 📊 LOG DELETE + TRANSCRIPT
    async def log_delete(self, interaction: discord.Interaction):

        log_channel = interaction.guild.get_channel(LOG_CHANNEL_ID)

        if not log_channel:
            return

        file_name = await self.create_transcript(interaction.channel)

        await log_channel.send(
            content=f"📊 Ticket deleted: {interaction.channel.name} by {interaction.user.mention}",
            file=discord.File(file_name)
        )

        # ❌ delete local file
        try:
            os.remove(file_name)
        except:
            pass


async def setup(bot):
    await bot.add_cog(TicketLogs(bot))

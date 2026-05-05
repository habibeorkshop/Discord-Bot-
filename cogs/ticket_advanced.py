import discord
from discord.ext import commands
from discord import app_commands
import io
from datetime import datetime

# 🔧 CONFIG
GUILD_ID = 1493552564799672320
STAFF_ROLE = 1493559145876557955
LOG_CHANNEL_ID = 1493574858687123527


# ================= TRANSCRIPT =================

async def create_transcript(channel: discord.TextChannel):
    messages = []
    async for msg in channel.history(limit=None, oldest_first=True):
        time = msg.created_at.strftime("%Y-%m-%d %H:%M")
        messages.append(f"[{time}] {msg.author}: {msg.content}")

    transcript_text = "\n".join(messages)
    file = discord.File(
        io.BytesIO(transcript_text.encode()),
        filename=f"{channel.name}-transcript.txt"
    )
    return file


# ================= BUTTON VIEW =================

class CloseView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(label=" Reopen", emoji="🔓", style=discord.ButtonStyle.secondary)
    async def reopen(self, interaction: discord.Interaction, button: discord.ui.Button):

        await interaction.channel.set_permissions(
            interaction.guild.default_role,
            send_messages=True
        )

        await interaction.response.send_message("🔓 Ticket reopened.")

    @discord.ui.button(label=" Delete", emoji="🗑️", style=discord.ButtonStyle.secondary)
    async def delete(self, interaction: discord.Interaction, button: discord.ui.Button):

        if STAFF_ROLE not in [r.id for r in interaction.user.roles]:
            return await interaction.response.send_message("❌ Staff only", ephemeral=True)

        await interaction.response.send_message("🗑️ Deleting ticket...")

        # 📜 TRANSCRIPT
        transcript = await create_transcript(interaction.channel)

        log_channel = interaction.guild.get_channel(LOG_CHANNEL_ID)
        if log_channel:
            await log_channel.send(
                f"🗑️ Ticket deleted: {interaction.channel.name}",
                file=transcript
            )

        await interaction.channel.delete()


# ================= COG =================

class AdvancedTickets(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.bot.add_view(CloseView())  # persistent buttons

    # 🔒 STAFF CHECK
    def is_staff(self, interaction):
        return STAFF_ROLE in [r.id for r in interaction.user.roles]

    # ================= CLOSE =================
    @app_commands.command(name="closeticket", description="Close ticket with options")
    @app_commands.guilds(discord.Object(id=GUILD_ID))
    async def closeticket(self, interaction: discord.Interaction):

        await interaction.response.defer()

        if not self.is_staff(interaction):
            return await interaction.followup.send("❌ Staff only", ephemeral=True)

        # 🔐 LOCK CHANNEL
        await interaction.channel.set_permissions(
            interaction.guild.default_role,
            send_messages=False
        )

        # 📜 TRANSCRIPT
        transcript = await create_transcript(interaction.channel)

        log_channel = interaction.guild.get_channel(LOG_CHANNEL_ID)
        if log_channel:
            await log_channel.send(
                f"🔒 Ticket closed: {interaction.channel.name}",
                file=transcript
            )

        await interaction.followup.send(
            "🔒 Ticket closed.\nChoose an option below:",
            view=CloseView()
        )

    # ================= DELETE COMMAND =================
    @app_commands.command(name="deleteticket", description="Delete ticket (safe confirm)")
    @app_commands.guilds(discord.Object(id=GUILD_ID))
    async def deleteticket(self, interaction: discord.Interaction):

        await interaction.response.defer(ephemeral=True)

        if not self.is_staff(interaction):
            return await interaction.followup.send("❌ Staff only")

        await interaction.followup.send(
            "⚠️ Are you sure you want to delete this ticket?\nUse the button below.",
            view=CloseView()
        )


async def setup(bot):
    await bot.add_cog(AdvancedTickets(bot))


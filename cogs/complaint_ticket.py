import discord
from discord.ext import commands
from discord import app_commands
import json
import os

# 🔧 CONFIG
CATEGORY_ID = 1493574775992225832
STAFF_ROLE = 1493559145876557955
COMPLAINT_ROLE = 1493562584354521199  # change if needed
GUILD_ID = 1493552564799672320

COUNTER_FILE = "ticket_counter.json"


# ================= COUNTER =================

def get_ticket_number():
    if not os.path.exists(COUNTER_FILE):
        with open(COUNTER_FILE, "w") as f:
            json.dump({"count": 0}, f)

    with open(COUNTER_FILE, "r") as f:
        data = json.load(f)

    data["count"] += 1

    with open(COUNTER_FILE, "w") as f:
        json.dump(data, f)

    return f"{data['count']:03}"


# ================= BUTTONS =================

class ComplaintButtons(discord.ui.View):
    def __init__(self, author):
        super().__init__(timeout=None)
        self.author = author

    @discord.ui.button(
        label=" Claim",
        emoji="👨‍✈️",
        style=discord.ButtonStyle.secondary,
        custom_id="complaint_claim"
    )
    async def claim(self, interaction: discord.Interaction, button: discord.ui.Button):

        if STAFF_ROLE not in [r.id for r in interaction.user.roles]:
            return await interaction.response.send_message("❌ Staff only", ephemeral=True)

        author_mention = self.author.mention if self.author else "Unknown User"

        embed = interaction.message.embeds[0]
        embed.description = (
            f"{author_mention}, your complaint is being reviewed.\n\n"
            f"📌 Please provide full details and evidence.\n\n"
            f"👤 Opened by: {author_mention}\n"
            f"👨‍✈️ Claimed by: {interaction.user.mention}"
        )

        await interaction.message.edit(embed=embed, view=self)
        await interaction.response.send_message(f"✅ Claimed by {interaction.user.mention}")

    @discord.ui.button(
        label=" Close",
        emoji="🔒",
        style=discord.ButtonStyle.secondary,
        custom_id="complaint_close"
    )
    async def close(self, interaction: discord.Interaction, button: discord.ui.Button):

        if STAFF_ROLE not in [r.id for r in interaction.user.roles]:
            return await interaction.response.send_message("❌ Staff only", ephemeral=True)

        await interaction.channel.set_permissions(
            interaction.guild.default_role,
            send_messages=False
        )

        await interaction.response.send_message(
            "🔒 Complaint closed.",
            view=ComplaintCloseView()
        )


# ================= CLOSE VIEW =================

class ComplaintCloseView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(
        label=" Reopen",
        emoji="🔓",
        style=discord.ButtonStyle.secondary,
        custom_id="complaint_reopen"
    )
    async def reopen(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.channel.set_permissions(
            interaction.guild.default_role,
            send_messages=True
        )
        await interaction.response.send_message("🔓 Reopened.")

    @discord.ui.button(
        label=" Delete",
        emoji="🗑️",
        style=discord.ButtonStyle.secondary,
        custom_id="complaint_delete"
    )
    async def delete(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_message("🗑️ Deleting...")
        await interaction.channel.delete()


# ================= PANEL =================

class ComplaintPanel(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(
        label=" File Complaint",
        emoji="⚠️",
        style=discord.ButtonStyle.secondary,
        custom_id="complaint_open"
    )
    async def open_ticket(self, interaction: discord.Interaction, button: discord.ui.Button):

        guild = interaction.guild
        user = interaction.user

        ticket_number = get_ticket_number()

        channel = await guild.create_text_channel(
            name=f"complaint-{ticket_number}",
            category=guild.get_channel(CATEGORY_ID),
            overwrites={
                guild.default_role: discord.PermissionOverwrite(view_channel=False),
                user: discord.PermissionOverwrite(view_channel=True, send_messages=True),
                guild.get_role(COMPLAINT_ROLE): discord.PermissionOverwrite(view_channel=True)
            }
        )

        embed = discord.Embed(
            title="⚠️ Staff / Pilot Complaint",
            description=(
                f"{user.mention}, please describe your complaint in detail.\n"
                f"Attach evidence if possible.\n\n"
                f"👤 Opened by: {user.mention}\n"
                f"👨‍✈️ Claimed by: Not yet"
            ),
            color=discord.Color.red()
        )

        await channel.send(
            content=f"<@&{COMPLAINT_ROLE}>",
            embed=embed,
            view=ComplaintButtons(user)
        )

        await interaction.response.send_message(
            f"✅ Complaint created: {channel.mention}",
            ephemeral=True
        )


# ================= COG =================

class ComplaintTicket(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

        self.bot.add_view(ComplaintPanel())
        self.bot.add_view(ComplaintCloseView())

    @app_commands.command(name="complaintpanel", description="Send Complaint panel")
    @app_commands.guilds(discord.Object(id=GUILD_ID))
    async def complaintpanel(self, interaction: discord.Interaction, channel: discord.TextChannel):

        if STAFF_ROLE not in [r.id for r in interaction.user.roles]:
            return await interaction.response.send_message("❌ Staff only", ephemeral=True)

        embed = discord.Embed(
            title="⚠️ Complaint System",
            description=(
                "Need to report an issue?\n\n"
                "Click below to file a complaint against staff/pilot.\n"
                "Provide full details for proper review."
            ),
            color=discord.Color.red()
        )

        await channel.send(embed=embed, view=ComplaintPanel())

        await interaction.response.send_message("✅ Complaint panel sent!", ephemeral=True)


async def setup(bot):
    await bot.add_cog(ComplaintTicket(bot))

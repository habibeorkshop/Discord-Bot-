import discord
from discord.ext import commands
from discord import app_commands
import json
import os

# 🔧 CONFIG
CATEGORY_ID = 1493574775992225832
STAFF_ROLE = 1493559145876557955

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

class TicketButtons(discord.ui.View):
    def __init__(self, author):
        super().__init__(timeout=None)
        self.author = author

    @discord.ui.button(label=" Claim", emoji="👨‍✈️", style=discord.ButtonStyle.secondary, custom_id="claim_btn")
    async def claim(self, interaction: discord.Interaction, button: discord.ui.Button):

        if STAFF_ROLE not in [r.id for r in interaction.user.roles]:
            return await interaction.response.send_message("❌ Staff only", ephemeral=True)

        embed = interaction.message.embeds[0]

        embed.description = (
            f"{self.author.mention} please describe your issue.\n"
            f"Our staff team will assist you shortly.\n\n"
            f"👤 Opened by: {self.author.mention}\n"
            f"👨‍✈️ Claimed by: {interaction.user.mention}"
        )

        await interaction.message.edit(embed=embed, view=self)

        await interaction.response.send_message(f"✅ Claimed by {interaction.user.mention}")

    @discord.ui.button(label=" Close", emoji="🔒", style=discord.ButtonStyle.secondary, custom_id="close_btn")
    async def close(self, interaction: discord.Interaction, button: discord.ui.Button):

        if STAFF_ROLE not in [r.id for r in interaction.user.roles]:
            return await interaction.response.send_message("❌ Staff only", ephemeral=True)

        await interaction.channel.set_permissions(interaction.guild.default_role, send_messages=False)

        await interaction.response.send_message(
            "🔒 Ticket closed. Choose an option:",
            view=CloseView()
        )


# ================= CLOSE VIEW =================

class CloseView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(label=" Reopen", emoji="🔓", style=discord.ButtonStyle.secondary, custom_id="reopen_btn")
    async def reopen(self, interaction: discord.Interaction, button: discord.ui.Button):

        await interaction.channel.set_permissions(interaction.guild.default_role, send_messages=True)
        await interaction.response.send_message("🔓 Ticket reopened.")

    @discord.ui.button(label=" Delete", emoji="🗑️", style=discord.ButtonStyle.secondary, custom_id="delete_btn")
    async def delete(self, interaction: discord.Interaction, button: discord.ui.Button):

        await interaction.response.send_message("🗑️ Deleting ticket...")
        await interaction.channel.delete()


# ================= PANEL =================

class PanelView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(label=" Open Ticket", emoji="🎫", style=discord.ButtonStyle.secondary, custom_id="open_ticket")
    async def open_ticket(self, interaction: discord.Interaction, button: discord.ui.Button):

        guild = interaction.guild
        category = guild.get_channel(CATEGORY_ID)
        user = interaction.user

        ticket_number = get_ticket_number()
        channel_name = f"ticket-{ticket_number}"

        overwrites = {
            guild.default_role: discord.PermissionOverwrite(view_channel=False),
            user: discord.PermissionOverwrite(view_channel=True, send_messages=True),
            guild.get_role(STAFF_ROLE): discord.PermissionOverwrite(view_channel=True, send_messages=True)
        }

        channel = await guild.create_text_channel(
            name=channel_name,
            category=category,
            overwrites=overwrites
        )

        # 📝 OLD STYLE EMBED + SMALL UPGRADE
        embed = discord.Embed(
            title="🎫 Support Ticket",
            description=(
                f"{user.mention} please describe your issue.\n"
                f"Our staff team will assist you shortly.\n\n"
                f"⏱️ Please be patient while we review your request.\n\n"
                f"👤 Opened by: {user.mention}\n"
                f"👨‍✈️ Claimed by: Not yet"
            ),
            color=discord.Color.orange()
        )

        await channel.send(
            content=f"<@&{STAFF_ROLE}>",  # 🔔 role ping outside embed
            embed=embed,
            view=TicketButtons(user)
        )

        await interaction.response.send_message(
            f"✅ Ticket created: {channel.mention}",
            ephemeral=True
        )


# ================= COG =================

class GeneralTicket(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

        # 🔁 persistent views
        self.bot.add_view(PanelView())
        self.bot.add_view(TicketButtons(None))
        self.bot.add_view(CloseView())

    @app_commands.command(name="generalpanel", description="Send General Support panel")
    async def generalpanel(self, interaction: discord.Interaction, channel: discord.TextChannel):

        # 🔐 ONLY STAFF ROLE
        if STAFF_ROLE not in [r.id for r in interaction.user.roles]:
            return await interaction.response.send_message("❌ Staff only", ephemeral=True)

        embed = discord.Embed(
            title="🎫 General Support",
            description=(
                "Need help? Open a support ticket below.\n\n"
                "📌 Click the button to create a private ticket.\n"
                "👨‍✈️ Our staff team will assist you shortly."
            ),
            color=discord.Color.red()
        )

        await channel.send(embed=embed, view=PanelView())

        await interaction.response.send_message("✅ Panel sent!", ephemeral=True)


async def setup(bot):
    await bot.add_cog(GeneralTicket(bot))
    

import discord
from discord.ext import commands
from discord import app_commands
import json
import os

# 🔧 CONFIG
CATEGORY_ID = 1493574775992225832
STAFF_ROLE = 1493559145876557955
RECRUIT_ROLE = 1493574929877172455
COMPLAINT_ROLE = 1493562584354521199
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


# ================= CLOSE VIEW =================
class CloseView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(label=" Reopen", emoji="🔓", style=discord.ButtonStyle.secondary, custom_id="ticket_reopen")
    async def reopen(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.channel.set_permissions(interaction.guild.default_role, send_messages=True)
        await interaction.response.send_message("🔓 Ticket reopened.")

    @discord.ui.button(label=" Delete", emoji="🗑️", style=discord.ButtonStyle.secondary, custom_id="ticket_delete")
    async def delete(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_message("🗑️ Deleting ticket...")
        await interaction.channel.delete()


# ================= BUTTONS =================
class TicketButtons(discord.ui.View):
    def __init__(self, author):
        super().__init__(timeout=None)
        self.author = author

    @discord.ui.button(label=" Claim", emoji="👨‍✈️", style=discord.ButtonStyle.secondary, custom_id="ticket_claim")
    async def claim(self, interaction: discord.Interaction, button: discord.ui.Button):

        if STAFF_ROLE not in [r.id for r in interaction.user.roles]:
            return await interaction.response.send_message("❌ Staff only", ephemeral=True)

        embed = interaction.message.embeds[0]

        embed.description = (
            f"{self.author.mention}\n\n"
            f"👤 Opened by: {self.author.mention}\n"
            f"👨‍✈️ Claimed by: {interaction.user.mention}\n\n"
            f"Our staff will assist you shortly."
        )

        await interaction.message.edit(embed=embed, view=self)
        await interaction.response.send_message(f"✅ Claimed by {interaction.user.mention}")

    @discord.ui.button(label=" Close", emoji="🔒", style=discord.ButtonStyle.secondary, custom_id="ticket_close")
    async def close(self, interaction: discord.Interaction, button: discord.ui.Button):

        if STAFF_ROLE not in [r.id for r in interaction.user.roles]:
            return await interaction.response.send_message("❌ Staff only", ephemeral=True)

        await interaction.channel.set_permissions(interaction.guild.default_role, send_messages=False)

        await interaction.response.send_message(
            "🔒 Ticket closed. Choose option:",
            view=CloseView()
        )


# ================= DROPDOWN =================
class TicketDropdown(discord.ui.Select):
    def __init__(self):
        options = [
            discord.SelectOption(label="General Support", emoji="🎫"),
            discord.SelectOption(label="Recruitment", emoji="🧑‍✈️"),
            discord.SelectOption(label="Complaint", emoji="⚠️")
        ]

        super().__init__(
            placeholder="Select ticket type...",
            min_values=1,
            max_values=1,
            options=options,
            custom_id="ticket_dropdown"
        )

    async def callback(self, interaction: discord.Interaction):
        guild = interaction.guild
        user = interaction.user
        category = guild.get_channel(CATEGORY_ID)

        ticket_number = get_ticket_number()
        channel_name = f"ticket-{ticket_number}"

        selected = self.values[0]

        # 🎯 ROLE + TEXT CONFIG
        if selected == "Recruitment":
            role = RECRUIT_ROLE
            title = "🧑‍✈️ Recruitment Ticket"
            desc = "Please provide your recruitment details."

        elif selected == "Complaint":
            role = COMPLAINT_ROLE
            title = "⚠️ Complaint Ticket"
            desc = "Describe your complaint with evidence."

        else:
            role = STAFF_ROLE
            title = "🎫 Support Ticket"
            desc = "Describe your issue."

        overwrites = {
            guild.default_role: discord.PermissionOverwrite(view_channel=False),
            user: discord.PermissionOverwrite(view_channel=True, send_messages=True),
            guild.get_role(role): discord.PermissionOverwrite(view_channel=True, send_messages=True)
        }

        channel = await guild.create_text_channel(
            name=channel_name,
            category=category,
            overwrites=overwrites
        )

        embed = discord.Embed(
            title=title,
            description=(
                f"{user.mention} {desc}\n\n"
                f"👤 Opened by: {user.mention}\n"
                f"👨‍✈️ Claimed by: Not yet"
            ),
            color=discord.Color.orange()
        )

        await channel.send(
            content=f"<@&{role}>",
            embed=embed,
            view=TicketButtons(user)
        )

        await interaction.response.send_message(
            f"✅ Ticket created: {channel.mention}",
            ephemeral=True
        )


# ================= PANEL VIEW =================
class TicketPanel(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)
        self.add_item(TicketDropdown())


# ================= COG =================
class TicketSystem(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

        # ✅ persistent views
        self.bot.add_view(TicketPanel())
        self.bot.add_view(CloseView())

    @app_commands.command(name="ticketpanel", description="Send ticket panel")
    @app_commands.guilds(discord.Object(id=GUILD_ID))
    async def ticketpanel(self, interaction: discord.Interaction, channel: discord.TextChannel):

        if STAFF_ROLE not in [r.id for r in interaction.user.roles]:
            return await interaction.response.send_message("❌ Staff only", ephemeral=True)

        embed = discord.Embed(
            title="🎫 Support Center",
            description=(
                "Welcome to support system ✈️\n\n"
                "Select a category below:\n\n"
                "🎫 General Support\n"
                "🧑‍✈️ Recruitment\n"
                "⚠️ Complaint\n\n"
                "Our team is available 24×7."
            ),
            color=discord.Color.red()
        )

        await channel.send(embed=embed, view=TicketPanel())

        await interaction.response.send_message("✅ Panel sent!", ephemeral=True)


async def setup(bot):
    await bot.add_cog(TicketSystem(bot))

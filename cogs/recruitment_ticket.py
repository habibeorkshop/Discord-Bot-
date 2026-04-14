import discord
from discord.ext import commands
from discord import app_commands
import json
import os

# 🔧 CONFIG
CATEGORY_ID = 1493574775992225832
STAFF_ROLE = 1493559145876557955
RECRUIT_ROLE = 1493574929877172455
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

class RecruitButtons(discord.ui.View):
    def __init__(self, author: discord.Member):
        super().__init__(timeout=None)
        self.author = author

    @discord.ui.button(label=" Claim", emoji="👨‍✈️", style=discord.ButtonStyle.secondary)
    async def claim(self, interaction: discord.Interaction, button: discord.ui.Button):

        if STAFF_ROLE not in [r.id for r in interaction.user.roles]:
            return await interaction.response.send_message("❌ Staff only", ephemeral=True)

        author_mention = self.author.mention if self.author else "Unknown User"

        embed = interaction.message.embeds[0]
        embed.description = (
            f"{author_mention} please provide your recruitment details.\n"
            f"Our recruitment team will assist you shortly.\n\n"
            f"👤 Opened by: {author_mention}\n"
            f"👨‍✈️ Claimed by: {interaction.user.mention}"
        )

        await interaction.message.edit(embed=embed, view=self)
        await interaction.response.send_message(f"✅ Claimed by {interaction.user.mention}")

    @discord.ui.button(label=" Close", emoji="🔒", style=discord.ButtonStyle.secondary)
    async def close(self, interaction: discord.Interaction, button: discord.ui.Button):

        if STAFF_ROLE not in [r.id for r in interaction.user.roles]:
            return await interaction.response.send_message("❌ Staff only", ephemeral=True)

        await interaction.channel.set_permissions(
            interaction.guild.default_role,
            send_messages=False
        )

        await interaction.response.send_message(
            "🔒 Ticket closed.",
            view=RecruitCloseView()
        )


# ================= CLOSE VIEW =================

class RecruitCloseView(discord.ui.View):
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
        await interaction.response.send_message("🗑️ Deleting ticket...")
        await interaction.channel.delete()


# ================= PANEL =================

class RecruitPanel(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(label=" Open Recruitment Ticket", emoji="🧑‍✈️", style=discord.ButtonStyle.secondary)
    async def open_ticket(self, interaction: discord.Interaction, button: discord.ui.Button):

        guild = interaction.guild
        user = interaction.user
        category = guild.get_channel(CATEGORY_ID)

        ticket_number = get_ticket_number()
        channel_name = f"ticket-{ticket_number}"

        overwrites = {
            guild.default_role: discord.PermissionOverwrite(view_channel=False),
            user: discord.PermissionOverwrite(view_channel=True, send_messages=True),
            guild.get_role(RECRUIT_ROLE): discord.PermissionOverwrite(view_channel=True, send_messages=True)
        }

        channel = await guild.create_text_channel(
            name=channel_name,
            category=category,
            overwrites=overwrites
        )

        embed = discord.Embed(
            title="🧑‍✈️ Recruitment Ticket",
            description=(
                f"{user.mention} please provide your recruitment details.\n"
                f"Our recruitment team will assist you shortly.\n\n"
                f"👤 Opened by: {user.mention}\n"
                f"👨‍✈️ Claimed by: Not yet"
            ),
            color=discord.Color.orange()
        )

        await channel.send(
            content=f"<@&{RECRUIT_ROLE}>",
            embed=embed,
            view=RecruitButtons(user)
        )

        await interaction.response.send_message(
            f"✅ Recruitment ticket created: {channel.mention}",
            ephemeral=True
        )


# ================= COG =================

class RecruitmentTicket(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

        # ✅ ONLY SAFE VIEWS
        self.bot.add_view(RecruitPanel())
        self.bot.add_view(RecruitCloseView())

    @app_commands.command(name="recruitpanel", description="Send Recruitment panel")
    @app_commands.guilds(discord.Object(id=GUILD_ID))
    async def recruitpanel(self, interaction: discord.Interaction, channel: discord.TextChannel):

        if STAFF_ROLE not in [r.id for r in interaction.user.roles]:
            return await interaction.response.send_message("❌ Staff only", ephemeral=True)

        embed = discord.Embed(
            title="🧑‍✈️ Recruitment Support",
            description=(
                "Interested in joining?\n\n"
                "📌 Click the button below to open a recruitment ticket.\n"
                "👨‍✈️ Our recruitment team will assist you."
            ),
            color=discord.Color.red()
        )

        await channel.send(embed=embed, view=RecruitPanel())

        await interaction.response.send_message("✅ Recruitment panel sent!", ephemeral=True)


async def setup(bot):
    await bot.add_cog(RecruitmentTicket(bot))

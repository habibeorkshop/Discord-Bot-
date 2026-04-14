import discord
from discord.ext import commands
from discord import app_commands

# 🔧 CONFIG (EDIT THESE)
CATEGORY_ID = 1493574775992225832  # ticket category ID
GENERAL_ROLE = 1493574929877172455
RECRUIT_ROLE = 1493574929877172455

# 🎛️ Dropdown
class TicketSelect(discord.ui.Select):
    def __init__(self, bot):
        self.bot = bot

        options = [
            discord.SelectOption(label="General Support", value="general"),
            discord.SelectOption(label="Recruitment", value="recruitment"),
        ]

        super().__init__(placeholder="Select ticket type...", options=options)

    async def callback(self, interaction: discord.Interaction):
        guild = interaction.guild
        user = interaction.user

        category = guild.get_channel(CATEGORY_ID)

        # 🔒 Check if user already has ticket
        for ch in category.text_channels:
            if str(user.id) in ch.name:
                await interaction.response.send_message(
                    "❌ You already have an open ticket!",
                    ephemeral=True
                )
                return

        # 🎯 Role + name
        if self.values[0] == "general":
            role_id = GENERAL_ROLE
            name = "general"

        elif self.values[0] == "recruitment":
            role_id = RECRUIT_ROLE
            name = "recruit"

        role = guild.get_role(role_id)

        # 🔐 Permissions
        overwrites = {
            guild.default_role: discord.PermissionOverwrite(view_channel=False),
            user: discord.PermissionOverwrite(view_channel=True, send_messages=True),
            role: discord.PermissionOverwrite(view_channel=True, send_messages=True)
        }

        channel = await guild.create_text_channel(
            name=f"{name}-{user.name}",
            category=category,
            overwrites=overwrites
        )

        # 📩 Embed message
        embed = discord.Embed(
            title="🎫 Ticket Created",
            description=f"{user.mention}, support will be with you shortly.",
            color=discord.Color.green()
        )

        view = TicketButtons()

        await channel.send(content=role.mention, embed=embed, view=view)

        await interaction.response.send_message(
            f"✅ Ticket created: {channel.mention}",
            ephemeral=True
        )

# 🎛️ View for dropdown
class TicketView(discord.ui.View):
    def __init__(self, bot):
        super().__init__(timeout=None)
        self.add_item(TicketSelect(bot))

# 🔘 Buttons
class TicketButtons(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(label="Claim", style=discord.ButtonStyle.primary)
    async def claim(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_message(
            f"🔒 Ticket claimed by {interaction.user.mention}"
        )

    @discord.ui.button(label="Close", style=discord.ButtonStyle.danger)
    async def close(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_message("❌ Closing ticket...")
        await interaction.channel.delete()

# 🧠 Cog
class Ticket(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="ticket", description="Create ticket panel")
    @app_commands.describe(channel="Channel to send panel", image="Optional image URL")
    async def ticket_panel(self, interaction: discord.Interaction, channel: discord.TextChannel, image: str = None):

        # 🔒 Staff only
        if not interaction.user.guild_permissions.manage_guild:
            await interaction.response.send_message(
                "❌ No permission",
                ephemeral=True
            )
            return

        embed = discord.Embed(
            title="🎫 Support Panel",
            description="Select a category below to open a ticket.",
            color=discord.Color.blue()
        )

        if image:
            embed.set_image(url=image)

        view = TicketView(self.bot)

        await channel.send(embed=embed, view=view)

        await interaction.response.send_message(
            "✅ Ticket panel created!",
            ephemeral=True
        )

async def setup(bot):
    await bot.add_cog(Ticket(bot))

import discord
from discord.ext import commands
from discord import app_commands

STAFF_ROLE_ID = 1493559145876557955

# 🎛️ Dropdown
class StatusSelect(discord.ui.Select):
    def __init__(self, bot, text):
        self.bot = bot
        self.text = text

        options = [
            discord.SelectOption(label="Playing", value="playing"),
            discord.SelectOption(label="Watching", value="watching"),
            discord.SelectOption(label="Listening", value="listening"),
        ]

        super().__init__(placeholder="Choose status type...", options=options)

    async def callback(self, interaction: discord.Interaction):
        # 🔒 Role check
        if STAFF_ROLE_ID not in [role.id for role in interaction.user.roles]:
            await interaction.response.send_message(
                "❌ You are not allowed to use this.",
                ephemeral=True
            )
            return

        choice = self.values[0]

        if choice == "playing":
            activity = discord.Game(name=self.text)

        elif choice == "watching":
            activity = discord.Activity(
                type=discord.ActivityType.watching,
                name=self.text
            )

        elif choice == "listening":
            activity = discord.Activity(
                type=discord.ActivityType.listening,
                name=self.text
            )

        await self.bot.change_presence(activity=activity)

        await interaction.response.send_message(
            f"✅ Status updated to {choice} {self.text}"
        )

# 🎛️ View
class StatusView(discord.ui.View):
    def __init__(self, bot, text):
        super().__init__(timeout=60)
        self.add_item(StatusSelect(bot, text))

# 🧠 Cog
class Status(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="status", description="Change bot status with dropdown")
    @app_commands.describe(text="Status text")
    async def status(self, interaction: discord.Interaction, text: str):

        # 🔒 Role check
        if STAFF_ROLE_ID not in [role.id for role in interaction.user.roles]:
            await interaction.response.send_message(
                "❌ You don't have permission.",
                ephemeral=True
            )
            return

        view = StatusView(self.bot, text)

        await interaction.response.send_message(
            "🎛️ Select the status type:",
            view=view,
            ephemeral=True
        )

async def setup(bot):
    await bot.add_cog(Status(bot))

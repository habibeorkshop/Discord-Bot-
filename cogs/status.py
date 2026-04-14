import discord
from discord.ext import commands
from discord import app_commands

class Status(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="status", description="Change bot status")
    async def status(self, interaction: discord.Interaction, text: str):
        await self.bot.change_presence(activity=discord.Game(name=text))
        await interaction.response.send_message(f"✅ Status changed to {text}")

async def setup(bot):
    await bot.add_cog(Status(bot))

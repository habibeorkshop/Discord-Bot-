import discord
from discord.ext import commands
from discord import app_commands

# 🔧 CONFIG
STAFF_ROLE = 1493559145876557955
GUILD_ID = 1493552564799672320


class Say(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="say", description="Send a message to a channel")
    @app_commands.guilds(discord.Object(id=GUILD_ID))
    async def say(
        self,
        interaction: discord.Interaction,
        channel: discord.TextChannel,
        message: str
    ):

        # 🔐 Staff only
        if STAFF_ROLE not in [role.id for role in interaction.user.roles]:
            return await interaction.response.send_message(
                "❌ You are not allowed to use this command.",
                ephemeral=True
            )

        await channel.send(message)

        await interaction.response.send_message(
            f"✅ Message sent in {channel.mention}",
            ephemeral=True
        )


async def setup(bot):
    await bot.add_cog(Say(bot))

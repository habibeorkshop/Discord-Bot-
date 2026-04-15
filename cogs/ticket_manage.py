import discord
from discord.ext import commands
from discord import app_commands

# 🔧 CONFIG
STAFF_ROLE = 1493559145876557955
GUILD_ID = 1493552564799672320


class TicketManage(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    # ➕ ADD USER
    @app_commands.command(name="adduser", description="Add a user to the ticket")
    @app_commands.guilds(discord.Object(id=GUILD_ID))
    async def adduser(self, interaction: discord.Interaction, member: discord.Member):

        # 🔐 Staff only
        if STAFF_ROLE not in [r.id for r in interaction.user.roles]:
            return await interaction.response.send_message(
                "❌ Staff only",
                ephemeral=True
            )

        # 🛑 Check ticket channel
        if not interaction.channel.name.startswith("ticket-"):
            return await interaction.response.send_message(
                "❌ This is not a ticket channel.",
                ephemeral=True
            )

        await interaction.channel.set_permissions(
            member,
            view_channel=True,
            send_messages=True
        )

        await interaction.response.send_message(
            f"✅ {member.mention} added to this ticket"
        )

    # ➖ REMOVE USER
    @app_commands.command(name="removeuser", description="Remove a user from the ticket")
    @app_commands.guilds(discord.Object(id=GUILD_ID))
    async def removeuser(self, interaction: discord.Interaction, member: discord.Member):

        # 🔐 Staff only
        if STAFF_ROLE not in [r.id for r in interaction.user.roles]:
            return await interaction.response.send_message(
                "❌ Staff only",
                ephemeral=True
            )

        # 🛑 Check ticket channel
        if not interaction.channel.name.startswith("ticket-"):
            return await interaction.response.send_message(
                "❌ This is not a ticket channel.",
                ephemeral=True
            )

        await interaction.channel.set_permissions(member, overwrite=None)

        await interaction.response.send_message(
            f"❌ {member.mention} removed from this ticket"
        )


async def setup(bot):
    await bot.add_cog(TicketManage(bot))

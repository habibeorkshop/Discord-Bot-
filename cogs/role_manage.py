import discord
from discord.ext import commands
from discord import app_commands

# 🔧 CONFIG
STAFF_ROLE = 1493559145876557955
GUILD_ID = 1493552564799672320


class RoleManage(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    # ➕ ADD ROLE
    @app_commands.command(name="addrole", description="Add a role to a user")
    @app_commands.guilds(discord.Object(id=GUILD_ID))
    async def addrole(
        self,
        interaction: discord.Interaction,
        member: discord.Member,
        role: discord.Role
    ):

        # 🔐 Staff only
        if STAFF_ROLE not in [r.id for r in interaction.user.roles]:
            return await interaction.response.send_message(
                "❌ Staff only",
                ephemeral=True
            )

        try:
            await member.add_roles(role)

            await interaction.response.send_message(
                f"✅ Added {role.mention} to {member.mention}"
            )

        except discord.Forbidden:
            await interaction.response.send_message(
                "❌ I don't have permission to add this role.",
                ephemeral=True
            )

    # ➖ REMOVE ROLE
    @app_commands.command(name="removerole", description="Remove a role from a user")
    @app_commands.guilds(discord.Object(id=GUILD_ID))
    async def removerole(
        self,
        interaction: discord.Interaction,
        member: discord.Member,
        role: discord.Role
    ):

        # 🔐 Staff only
        if STAFF_ROLE not in [r.id for r in interaction.user.roles]:
            return await interaction.response.send_message(
                "❌ Staff only",
                ephemeral=True
            )

        try:
            await member.remove_roles(role)

            await interaction.response.send_message(
                f"❌ Removed {role.mention} from {member.mention}"
            )

        except discord.Forbidden:
            await interaction.response.send_message(
                "❌ I don't have permission to remove this role.",
                ephemeral=True
            )


async def setup(bot):
    await bot.add_cog(RoleManage(bot))

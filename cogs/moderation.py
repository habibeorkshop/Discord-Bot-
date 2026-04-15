import discord
from discord.ext import commands
from discord import app_commands

# 🔧 CONFIG
GUILD_ID = 1493552564799672320
STAFF_ROLE = 1493559145876557955


class Moderation(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    # 🔒 CHECK STAFF
    def is_staff(self, interaction: discord.Interaction):
        return STAFF_ROLE in [role.id for role in interaction.user.roles]

    # ================= KICK =================
    @app_commands.command(name="kick", description="Kick a member")
    @app_commands.guilds(discord.Object(id=GUILD_ID))
    async def kick(self, interaction: discord.Interaction, member: discord.Member, reason: str = "No reason"):

        if not self.is_staff(interaction):
            return await interaction.response.send_message("❌ Staff only", ephemeral=True)

        await member.kick(reason=reason)

        await interaction.response.send_message(
            f"👢 {member.mention} has been kicked.\nReason: {reason}"
        )

    # ================= BAN =================
    @app_commands.command(name="ban", description="Ban a member")
    @app_commands.guilds(discord.Object(id=GUILD_ID))
    async def ban(self, interaction: discord.Interaction, member: discord.Member, reason: str = "No reason"):

        if not self.is_staff(interaction):
            return await interaction.response.send_message("❌ Staff only", ephemeral=True)

        await member.ban(reason=reason)

        await interaction.response.send_message(
            f"🔨 {member.mention} has been banned.\nReason: {reason}"
        )

    # ================= TIMEOUT =================
    @app_commands.command(name="timeout", description="Timeout a member (minutes)")
    @app_commands.guilds(discord.Object(id=GUILD_ID))
    async def timeout(self, interaction: discord.Interaction, member: discord.Member, minutes: int, reason: str = "No reason"):

        if not self.is_staff(interaction):
            return await interaction.response.send_message("❌ Staff only", ephemeral=True)

        duration = discord.utils.utcnow() + discord.timedelta(minutes=minutes)

        await member.timeout(duration, reason=reason)

        await interaction.response.send_message(
            f"⏳ {member.mention} timed out for {minutes} minutes.\nReason: {reason}"
        )

    # ================= REMOVE TIMEOUT =================
    @app_commands.command(name="untimeout", description="Remove timeout")
    @app_commands.guilds(discord.Object(id=GUILD_ID))
    async def untimeout(self, interaction: discord.Interaction, member: discord.Member):

        if not self.is_staff(interaction):
            return await interaction.response.send_message("❌ Staff only", ephemeral=True)

        await member.timeout(None)

        await interaction.response.send_message(
            f"✅ Timeout removed for {member.mention}"
        )

    # ================= NICKNAME =================
    @app_commands.command(name="nick", description="Change nickname")
    @app_commands.guilds(discord.Object(id=GUILD_ID))
    async def nick(self, interaction: discord.Interaction, member: discord.Member, nickname: str):

        if not self.is_staff(interaction):
            return await interaction.response.send_message("❌ Staff only", ephemeral=True)

        await member.edit(nick=nickname)

        await interaction.response.send_message(
            f"✏️ {member.mention} nickname changed to **{nickname}**"
        )


async def setup(bot):
    await bot.add_cog(Moderation(bot))

import discord
from discord.ext import commands
from discord import app_commands
from datetime import timedelta

# 🔧 CONFIG
GUILD_ID = 1493552564799672320
STAFF_ROLE = 1493559145876557955


class Moderation(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    # 🔒 STAFF CHECK
    def is_staff(self, interaction: discord.Interaction):
        return STAFF_ROLE in [role.id for role in interaction.user.roles]

    # ================= KICK =================
    @app_commands.command(name="kick", description="Kick a member")
    @app_commands.guilds(discord.Object(id=GUILD_ID))
    async def kick(self, interaction: discord.Interaction, member: discord.Member, reason: str = "No reason"):

        await interaction.response.defer(ephemeral=True)

        if not self.is_staff(interaction):
            return await interaction.followup.send("❌ Staff only")

        try:
            await member.kick(reason=reason)
            await interaction.followup.send(f"👢 {member.mention} kicked\nReason: {reason}")
        except Exception as e:
            await interaction.followup.send(f"❌ Error: {e}")

    # ================= BAN =================
    @app_commands.command(name="ban", description="Ban a member")
    @app_commands.guilds(discord.Object(id=GUILD_ID))
    async def ban(self, interaction: discord.Interaction, member: discord.Member, reason: str = "No reason"):

        await interaction.response.defer(ephemeral=True)

        if not self.is_staff(interaction):
            return await interaction.followup.send("❌ Staff only")

        try:
            await member.ban(reason=reason)
            await interaction.followup.send(f"🔨 {member.mention} banned\nReason: {reason}")
        except Exception as e:
            await interaction.followup.send(f"❌ Error: {e}")

    # ================= TIMEOUT =================
    @app_commands.command(name="timeout", description="Timeout a member")
    @app_commands.guilds(discord.Object(id=GUILD_ID))
    async def timeout(self, interaction: discord.Interaction, member: discord.Member, minutes: int, reason: str = "No reason"):

        await interaction.response.defer(ephemeral=True)

        if not self.is_staff(interaction):
            return await interaction.followup.send("❌ Staff only")

        try:
            until = discord.utils.utcnow() + timedelta(minutes=minutes)
            await member.timeout(until, reason=reason)

            await interaction.followup.send(
                f"⏳ {member.mention} timed out for {minutes} minutes\nReason: {reason}"
            )
        except Exception as e:
            await interaction.followup.send(f"❌ Error: {e}")

    # ================= REMOVE TIMEOUT =================
    @app_commands.command(name="untimeout", description="Remove timeout")
    @app_commands.guilds(discord.Object(id=GUILD_ID))
    async def untimeout(self, interaction: discord.Interaction, member: discord.Member):

        await interaction.response.defer(ephemeral=True)

        if not self.is_staff(interaction):
            return await interaction.followup.send("❌ Staff only")

        try:
            await member.timeout(None)
            await interaction.followup.send(f"✅ Timeout removed for {member.mention}")
        except Exception as e:
            await interaction.followup.send(f"❌ Error: {e}")

    # ================= NICK =================
    @app_commands.command(name="nick", description="Change nickname")
    @app_commands.guilds(discord.Object(id=GUILD_ID))
    async def nick(self, interaction: discord.Interaction, member: discord.Member, nickname: str):

        await interaction.response.defer(ephemeral=True)

        if not self.is_staff(interaction):
            return await interaction.followup.send("❌ Staff only")

        try:
            await member.edit(nick=nickname)
            await interaction.followup.send(f"✏️ Nickname changed for {member.mention}")
        except Exception as e:
            await interaction.followup.send(f"❌ Error: {e}")


async def setup(bot):
    await bot.add_cog(Moderation(bot))
    

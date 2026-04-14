import discord
from discord.ext import commands

WELCOME_CHANNEL_ID = 1493569257953300640

class Welcome(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_member_join(self, member: discord.Member):
        channel = self.bot.get_channel(WELCOME_CHANNEL_ID)

        if not channel:
            return

        message = (
            f"✈️ Welcome to SpiceJet Virtual ❤️\n"
            f"Glad to have you onboard, Captain {member.mention} 👨‍✈️\n"
            f"Check rules and get ready for departure.\n"
            f"Clear skies! ✦"
        )

        await channel.send(message)

async def setup(bot):
    await bot.add_cog(Welcome(bot))

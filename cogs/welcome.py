import discord
from discord.ext import commands

WELCOME_CHANNEL_ID = 1493569257953300640
AUTO_ROLE_ID = 1500899502322745506


class Welcome(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_member_join(self, member: discord.Member):

        # ================= AUTO ROLE =================
        role = member.guild.get_role(AUTO_ROLE_ID)
        if role:
            try:
                await member.add_roles(role)
            except Exception as e:
                print(f"❌ Role error: {e}")

        # ================= DM MESSAGE =================
        dm_message = (
            "## ✈️ Welcome to SpiceJet Virtual ❤️\n\n"
            f"Hello Captain {member.name} 👨‍✈️\n\n"
            "We're excited to have you onboard!\n\n"
            "📌 **Get Started:**\n"
            "• Read the server rules\n"
            "• Explore available commands\n"
            "• Open a **Recruitment Ticket** to join the crew\n\n"
            "💬 Need help? Use our support system anytime.\n\n"
            "Clear skies and happy flying! ✦"
        )

        try:
            await member.send(dm_message)
        except discord.Forbidden:
            print(f"❌ Cannot DM {member.name}")
        except Exception as e:
            print(f"❌ DM error: {e}")

        # ================= CHANNEL MESSAGE =================
        channel = self.bot.get_channel(WELCOME_CHANNEL_ID)

        if not channel:
            return

        channel_message = (
            "## ✈️ Welcome to SpiceJet Virtual ❤️\n\n"
            f"Glad to have you onboard, Captain {member.mention} 👨‍✈️\n"
            "Please review the rules, explore commands, and get ready for departure.\n"
            "To join the crew, open an **“Open Recruitment Ticket”** in #tickets.\n"
            "Need help? Use the support system anytime.\n\n"
            "Clear skies and happy flying! ✦"
        )

        try:
            await channel.send(channel_message)
        except Exception as e:
            print(f"❌ Channel message error: {e}")


async def setup(bot):
    await bot.add_cog(Welcome(bot))

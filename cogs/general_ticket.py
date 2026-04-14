import discord
from discord.ext import commands
from discord import app_commands

# 🔧 CONFIG
CATEGORY_ID = 1493574775992225832
STAFF_ROLE = 1493559145876557955


# ================= BUTTON VIEW =================

class TicketButtons(discord.ui.View):
    def __init__(self, author):
        super().__init__(timeout=None)
        self.author = author
        self.claimed_by = None

    @discord.ui.button(label="Claim", style=discord.ButtonStyle.green, custom_id="gen_claim")
    async def claim(self, interaction: discord.Interaction, button: discord.ui.Button):

        if STAFF_ROLE not in [r.id for r in interaction.user.roles]:
            return await interaction.response.send_message("❌ Staff only", ephemeral=True)

        self.claimed_by = interaction.user

        embed = interaction.message.embeds[0]
        embed.description = (
            f"🛠️ Our staff members will contact you shortly\n\n"
            f"👤 Opened by: {self.author.mention}\n"
            f"👨‍✈️ Claimed by: {interaction.user.mention}"
        )

        await interaction.message.edit(embed=embed, view=self)
        await interaction.response.send_message(f"✅ Claimed by {interaction.user.mention}")

    @discord.ui.button(label="Close", style=discord.ButtonStyle.red, custom_id="gen_close")
    async def close(self, interaction: discord.Interaction, button: discord.ui.Button):

        if STAFF_ROLE not in [r.id for r in interaction.user.roles]:
            return await interaction.response.send_message("❌ Staff only", ephemeral=True)

        # 🔒 Lock channel (only staff can talk)
        await interaction.channel.set_permissions(interaction.guild.default_role, send_messages=False)

        await interaction.response.send_message(
            "🔒 Ticket closed. Choose an option:",
            view=CloseConfirmView()
        )


# ================= CLOSE CONFIRM =================

class CloseConfirmView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(label="Reopen", style=discord.ButtonStyle.green, custom_id="gen_reopen")
    async def reopen(self, interaction: discord.Interaction, button: discord.ui.Button):

        await interaction.channel.set_permissions(interaction.guild.default_role, send_messages=True)

        await interaction.response.send_message("🔓 Ticket reopened.")

    @discord.ui.button(label="Delete", style=discord.ButtonStyle.red, custom_id="gen_delete")
    async def delete(self, interaction: discord.Interaction, button: discord.ui.Button):

        await interaction.response.send_message("🗑️ Deleting ticket...")
        await interaction.channel.delete()


# ================= PANEL BUTTON =================

class GeneralPanelButton(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(label="Open General Support Ticket", style=discord.ButtonStyle.primary, custom_id="gen_open")
    async def open_ticket(self, interaction: discord.Interaction, button: discord.ui.Button):

        guild = interaction.guild
        category = guild.get_channel(CATEGORY_ID)
        user = interaction.user

        # 🎯 channel name
        channel_name = f"general-{user.name}-{user.id}"

        overwrites = {
            guild.default_role: discord.PermissionOverwrite(view_channel=False),
            user: discord.PermissionOverwrite(view_channel=True, send_messages=True),
            guild.get_role(STAFF_ROLE): discord.PermissionOverwrite(view_channel=True, send_messages=True)
        }

        channel = await guild.create_text_channel(
            name=channel_name,
            category=category,
            overwrites=overwrites
        )

        embed = discord.Embed(
            title="🎫 General Support",
            description=(
                f"🛠️ Our staff members will contact you shortly\n\n"
                f"👤 Opened by: {user.mention}\n"
                f"👨‍✈️ Claimed by: Not yet"
            ),
            color=discord.Color.orange()
        )

        await channel.send(embed=embed, view=TicketButtons(user))

        await interaction.response.send_message(
            f"✅ Ticket created: {channel.mention}",
            ephemeral=True
        )


# ================= COG =================

class GeneralTicket(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

        # 🔥 persistent views
        self.bot.add_view(GeneralPanelButton())
        self.bot.add_view(TicketButtons(None))
        self.bot.add_view(CloseConfirmView())

    @app_commands.command(name="generalpanel", description="Send General Support panel")
    async def generalpanel(self, interaction: discord.Interaction, channel: discord.TextChannel):

        if STAFF_ROLE not in [r.id for r in interaction.user.roles]:
            return await interaction.response.send_message("❌ Staff only", ephemeral=True)

        embed = discord.Embed(
            title="🎫 General Support",
            description="Click the button below to open a support ticket.",
            color=discord.Color.orange()
        )

        await channel.send(embed=embed, view=GeneralPanelButton())

        await interaction.response.send_message("✅ Panel sent!", ephemeral=True)


async def setup(bot):
    await bot.add_cog(GeneralTicket(bot))

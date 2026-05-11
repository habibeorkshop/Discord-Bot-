import discord
from discord.ext import commands
from discord import app_commands
import json
import os

# =========================================================
# 🔧 CONFIG
# =========================================================

GUILD_ID = 1493552564799672320

STAFF_ROLE = 1493559145876557955

PIREP_LOG_CHANNEL_ID = 1493812350908760065  # <-- ADD YOUR LOG CHANNEL ID

PIREP_FILE = "pireps.json"


# =========================================================
# 📁 JSON SYSTEM
# =========================================================

def load_json(path, default):
    if not os.path.exists(path):
        with open(path, "w") as f:
            json.dump(default, f)

    with open(path, "r") as f:
        return json.load(f)


def save_json(path, data):
    with open(path, "w") as f:
        json.dump(data, f, indent=4)


# =========================================================
# ✈️ ICAO VALIDATION
# =========================================================

def valid_icao(code):
    return len(code) == 4 and code.isalpha()


# =========================================================
# ✏️ EDIT MODAL
# =========================================================

class EditPirepModal(discord.ui.Modal, title="Edit PIREP"):

    comments = discord.ui.TextInput(
        label="Edit Comments",
        style=discord.TextStyle.paragraph,
        required=False
    )

    def __init__(self, pirep_id):
        super().__init__()
        self.pirep_id = pirep_id

    async def on_submit(self, interaction: discord.Interaction):

        pireps = load_json(PIREP_FILE, [])

        for p in pireps:
            if p["id"] == self.pirep_id:
                p["comments"] = self.comments.value

        save_json(PIREP_FILE, pireps)

        embed = interaction.message.embeds[0]

        found = False

        for i, field in enumerate(embed.fields):
            if field.name == "Comments":
                embed.set_field_at(
                    i,
                    name="Comments",
                    value=self.comments.value or "None",
                    inline=False
                )
                found = True

        if not found:
            embed.add_field(
                name="Comments",
                value=self.comments.value or "None",
                inline=False
            )

        await interaction.message.edit(embed=embed)

        await interaction.response.send_message(
            "✏️ PIREP updated.",
            ephemeral=True
        )


# =========================================================
# ✅ APPROVE / DENY BUTTONS
# =========================================================

class PirepButtons(discord.ui.View):
    def __init__(self, pirep_id: int, pilot_id: int):
        super().__init__(timeout=None)

        self.pirep_id = pirep_id
        self.pilot_id = pilot_id

    # =====================================================
    # ✅ APPROVE
    # =====================================================

    @discord.ui.button(
        label="Approve",
        emoji="✅",
        style=discord.ButtonStyle.success,
        custom_id="pirep_approve"
    )
    async def approve(self, interaction: discord.Interaction, button: discord.ui.Button):

        if STAFF_ROLE not in [r.id for r in interaction.user.roles]:
            return await interaction.response.send_message(
                "❌ Staff only.",
                ephemeral=True
            )

        pireps = load_json(PIREP_FILE, [])

        for p in pireps:
            if p["id"] == self.pirep_id:
                p["status"] = "Approved"
                p["reviewed_by"] = interaction.user.name

        save_json(PIREP_FILE, pireps)

        embed = interaction.message.embeds[0]

        embed.color = discord.Color.green()

        for i, field in enumerate(embed.fields):
            if field.name == "Status":
                embed.set_field_at(
                    i,
                    name="Status",
                    value=f"🟢 Approved by {interaction.user.mention}",
                    inline=False
                )

        await interaction.message.edit(embed=embed, view=self)

        user = interaction.guild.get_member(self.pilot_id)

        if user:
            try:
                await user.send(
                    f"✅ Your PIREP #{self.pirep_id} has been approved."
                )
            except:
                pass

        await interaction.response.send_message(
            "✅ PIREP approved.",
            ephemeral=True
        )

    # =====================================================
    # ❌ DENY
    # =====================================================

    @discord.ui.button(
        label="Deny",
        emoji="❌",
        style=discord.ButtonStyle.danger,
        custom_id="pirep_deny"
    )
    async def deny(self, interaction: discord.Interaction, button: discord.ui.Button):

        if STAFF_ROLE not in [r.id for r in interaction.user.roles]:
            return await interaction.response.send_message(
                "❌ Staff only.",
                ephemeral=True
            )

        pireps = load_json(PIREP_FILE, [])

        for p in pireps:
            if p["id"] == self.pirep_id:
                p["status"] = "Denied"
                p["reviewed_by"] = interaction.user.name

        save_json(PIREP_FILE, pireps)

        embed = interaction.message.embeds[0]

        embed.color = discord.Color.red()

        for i, field in enumerate(embed.fields):
            if field.name == "Status":
                embed.set_field_at(
                    i,
                    name="Status",
                    value=f"🔴 Denied by {interaction.user.mention}",
                    inline=False
                )

        await interaction.message.edit(embed=embed, view=self)

        user = interaction.guild.get_member(self.pilot_id)

        if user:
            try:
                await user.send(
                    f"❌ Your PIREP #{self.pirep_id} has been denied."
                )
            except:
                pass

        await interaction.response.send_message(
            "❌ PIREP denied.",
            ephemeral=True
        )

    # =====================================================
    # ✏️ EDIT
    # =====================================================

    @discord.ui.button(
        label="Edit",
        emoji="✏️",
        style=discord.ButtonStyle.secondary,
        custom_id="pirep_edit"
    )
    async def edit(self, interaction: discord.Interaction, button: discord.ui.Button):

        if STAFF_ROLE not in [r.id for r in interaction.user.roles]:
            return await interaction.response.send_message(
                "❌ Staff only.",
                ephemeral=True
            )

        await interaction.response.send_modal(
            EditPirepModal(self.pirep_id)
        )


# =========================================================
# 📝 PIREP MODAL
# =========================================================

class PirepModal(discord.ui.Modal, title="SGVA PIREP Centre"):

    flight_number = discord.ui.TextInput(
        label="Flight Number",
        placeholder="SG123"
    )

    route = discord.ui.TextInput(
        label="From - To",
        placeholder="VABB - OMDB"
    )

    aircraft = discord.ui.TextInput(
        label="Aircraft",
        placeholder="B737 MAX 8"
    )

    flight_time = discord.ui.TextInput(
        label="Flight Time",
        placeholder="2h 15m"
    )

    operator = discord.ui.TextInput(
        label="Operator | Multiplier | Comments",
        style=discord.TextStyle.paragraph,
        placeholder="SpiceJet | 1.5x | Smooth flight"
    )

    async def on_submit(self, interaction: discord.Interaction):

        try:
            dep, arr = [x.strip().upper() for x in self.route.value.split("-")]
        except:
            return await interaction.response.send_message(
                "❌ Invalid route format.",
                ephemeral=True
            )

        if not valid_icao(dep) or not valid_icao(arr):
            return await interaction.response.send_message(
                "❌ Invalid ICAO.",
                ephemeral=True
            )

        try:
            operator, multiplier, comments = [
                x.strip()
                for x in self.operator.value.split("|")
            ]
        except:
            return await interaction.response.send_message(
                "❌ Use:\nOperator | Multiplier | Comments",
                ephemeral=True
            )

        pireps = load_json(PIREP_FILE, [])

        pirep_id = len(pireps) + 1

        data = {
            "id": pirep_id,
            "user_id": interaction.user.id,
            "flight_number": self.flight_number.value,
            "departure": dep,
            "arrival": arr,
            "aircraft": self.aircraft.value,
            "flight_time": self.flight_time.value,
            "operator": operator,
            "multiplier": multiplier,
            "comments": comments,
            "status": "Pending"
        }

        pireps.append(data)

        save_json(PIREP_FILE, pireps)

        embed = discord.Embed(
            title=f"✈️ PIREP #{pirep_id}",
            color=discord.Color.orange()
        )

        embed.add_field(
            name="Flight Number",
            value=self.flight_number.value,
            inline=True
        )

        embed.add_field(
            name="From → To",
            value=f"{dep} → {arr}",
            inline=True
        )

        embed.add_field(
            name="Aircraft",
            value=self.aircraft.value,
            inline=True
        )

        embed.add_field(
            name="Flight Time",
            value=self.flight_time.value,
            inline=True
        )

        embed.add_field(
            name="Operator",
            value=operator,
            inline=True
        )

        embed.add_field(
            name="Multiplier",
            value=multiplier,
            inline=True
        )

        embed.add_field(
            name="Comments",
            value=comments or "None",
            inline=False
        )

        embed.add_field(
            name="Pilot",
            value=interaction.user.mention,
            inline=False
        )

        embed.add_field(
            name="Status",
            value="🟡 Pending Review",
            inline=False
        )

        log_channel = interaction.guild.get_channel(
            PIREP_LOG_CHANNEL_ID
        )

        await log_channel.send(
            embed=embed,
            view=PirepButtons(
                pirep_id,
                interaction.user.id
            )
        )

        await interaction.response.send_message(
            "✅ PIREP submitted successfully.",
            ephemeral=True
        )


# =========================================================
# 📤 PANEL BUTTON
# =========================================================

class PirepPanel(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(
        label="Submit PIREP",
        emoji="✈️",
        style=discord.ButtonStyle.secondary,
        custom_id="submit_pirep"
    )
    async def submit(self, interaction: discord.Interaction, button: discord.ui.Button):

        await interaction.response.send_modal(
            PirepModal()
        )


# =========================================================
# ✈️ COG
# =========================================================

class Pirep(commands.Cog):

    def __init__(self, bot):
        self.bot = bot

        self.bot.add_view(PirepPanel())

    # =====================================================
    # PANEL
    # =====================================================

    @app_commands.command(
        name="pirep-panel",
        description="Send PIREP panel"
    )
    @app_commands.guilds(discord.Object(id=GUILD_ID))
    async def pirep_panel(
        self,
        interaction: discord.Interaction,
        channel: discord.TextChannel
    ):

        if STAFF_ROLE not in [
            r.id for r in interaction.user.roles
        ]:
            return await interaction.response.send_message(
                "❌ Staff only.",
                ephemeral=True
            )

        embed = discord.Embed(
            title="✈️ SGVA PIREP Centre",
            description=(
                "Submit your completed flights here.\n\n"
                "📌 Include accurate flight information.\n"
                "📊 Staff will review your PIREP shortly."
            ),
            color=discord.Color.orange()
        )

        await channel.send(
            embed=embed,
            view=PirepPanel()
        )

        await interaction.response.send_message(
            "✅ PIREP panel sent.",
            ephemeral=True
        )

    # =====================================================
    # 📋 LIST
    # =====================================================

    @app_commands.command(
        name="pirep-list",
        description="View your recent PIREPs"
    )
    async def pirep_list(
        self,
        interaction: discord.Interaction
    ):

        pireps = load_json(PIREP_FILE, [])

        user_pireps = [
            p for p in pireps
            if p["user_id"] == interaction.user.id
        ][-10:]

        if not user_pireps:
            return await interaction.response.send_message(
                "❌ No PIREPs found.",
                ephemeral=True
            )

        lines = []

        for p in reversed(user_pireps):
            lines.append(
                f"#{p['id']} • "
                f"{p['departure']} → {p['arrival']} • "
                f"{p['aircraft']} • "
                f"{p['status']}"
            )

        await interaction.response.send_message(
            "## ✈️ Your Recent PIREPs\n\n"
            + "\n".join(lines),
            ephemeral=True
        )

    # =====================================================
    # 📊 STATS
    # =====================================================

    @app_commands.command(
        name="pirep-stats",
        description="View your PIREP stats"
    )
    async def pirep_stats(
        self,
        interaction: discord.Interaction
    ):

        pireps = load_json(PIREP_FILE, [])

        user_pireps = [
            p for p in pireps
            if p["user_id"] == interaction.user.id
        ]

        approved = len([
            p for p in user_pireps
            if p["status"] == "Approved"
        ])

        denied = len([
            p for p in user_pireps
            if p["status"] == "Denied"
        ])

        pending = len([
            p for p in user_pireps
            if p["status"] == "Pending"
        ])

        total = len(user_pireps)

        await interaction.response.send_message(
            f"""
# 📊 Your PIREP Statistics

✈️ Total Flights: {total}
🟢 Approved: {approved}
🟡 Pending: {pending}
🔴 Denied: {denied}

Pilot: {interaction.user.mention}
""",
            ephemeral=True
        )


# =========================================================
# 🔌 LOAD COG
# =========================================================

async def setup(bot):
    await bot.add_cog(Pirep(bot))

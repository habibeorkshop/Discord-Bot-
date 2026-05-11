# =========================================================
# ✈️ SGVA ADVANCED PIREP SYSTEM
# =========================================================
#
# ✅ FIXED SUBMIT BUTTON
# ✅ FIXED PERSISTENT VIEWS
# ✅ STATS SAVE AFTER RESTART
# ✅ ALL EMBEDS RED
# ✅ APPROVE / DENY / EDIT WORKING
# ✅ AUTO RANK SYSTEM
# ✅ AUTO ROLE SYSTEM
# ✅ PILOT STATS
# ✅ RECENT PIREPS
# ✅ DM NOTIFICATIONS
#
# FILE NAME:
# pirep.py
#
# =========================================================

import discord
from discord.ext import commands
from discord import app_commands
import json
import os
import re

# =========================================================
# 🔧 CONFIG
# =========================================================

GUILD_ID = 1493552564799672320

STAFF_ROLE = 1493559145876557955

PIREP_LOG_CHANNEL_ID = 1493812350908760065

# =========================================================
# 🏅 RANK ROLES
# =========================================================

RANK_ROLES = {
    0: 1500899695994601472,
    5: 1500900295637602495,
    15: 1500900431180599316,
    35: 1500900552438186236,
    60: 1500900613821694014,
    100: 1500900801176928467,
    200: 1500900874782769333,
}

# =========================================================
# 📁 DATABASE
# =========================================================

PIREP_FILE = "pireps.json"

# =========================================================
# 📁 JSON SYSTEM
# =========================================================

def load_json(path, default):

    if not os.path.exists(path):

        with open(path, "w") as f:
            json.dump(default, f)

    try:
        with open(path, "r") as f:
            return json.load(f)

    except:
        return default


def save_json(path, data):

    with open(path, "w") as f:
        json.dump(data, f, indent=4)

# =========================================================
# 🕒 TIME PARSER
# =========================================================

def parse_flight_time(time_str):

    time_str = str(time_str).lower()

    hours = 0
    minutes = 0

    h_match = re.search(r"(\d+)h", time_str)
    m_match = re.search(r"(\d+)m", time_str)

    if h_match:
        hours = int(h_match.group(1))

    if m_match:
        minutes = int(m_match.group(1))

    return (hours * 60) + minutes

# =========================================================
# 🏅 RANK SYSTEM
# =========================================================

def get_rank(total_hours):

    ranks = [
        (0, "Cadet"),
        (5, "Junior First Officer"),
        (15, "Senior First Officer"),
        (35, "Captain"),
        (60, "Senior Captain"),
        (100, "Chief Pilot"),
        (200, "Elite Pilot")
    ]

    current_rank = "Cadet"
    next_rank = None

    for req, rank in ranks:

        if total_hours >= req:
            current_rank = rank

        elif next_rank is None:
            next_rank = (req, rank)

    return current_rank, next_rank

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

        for i, field in enumerate(embed.fields):

            if field.name == "Comments":

                embed.set_field_at(
                    i,
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
# ✅ STAFF BUTTONS
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
        custom_id="pirep_approve_button"
    )
    async def approve(self, interaction: discord.Interaction, button: discord.ui.Button):

        if STAFF_ROLE not in [r.id for r in interaction.user.roles]:

            return await interaction.response.send_message(
                "❌ Staff only.",
                ephemeral=True
            )

        await interaction.response.defer(ephemeral=True)

        pireps = load_json(PIREP_FILE, [])

        found = False

        for p in pireps:

            if p["id"] == self.pirep_id:

                p["status"] = "Approved"
                p["reviewed_by"] = interaction.user.name

                found = True

        if not found:

            return await interaction.followup.send(
                "❌ PIREP not found.",
                ephemeral=True
            )

        save_json(PIREP_FILE, pireps)

        approved = [

            p for p in pireps

            if p["user_id"] == self.pilot_id
            and p["status"] == "Approved"

        ]

        total_minutes = sum(
            parse_flight_time(p["flight_time"])
            for p in approved
        )

        total_hours = round(total_minutes / 60, 1)

        rank_name, next_rank = get_rank(total_hours)

        member = interaction.guild.get_member(self.pilot_id)

        # =================================================
        # AUTO ROLE SYSTEM
        # =================================================

        if member:

            for role_id in RANK_ROLES.values():

                role = interaction.guild.get_role(role_id)

                if role and role in member.roles:
                    await member.remove_roles(role)

            best_role = None

            for req, role_id in RANK_ROLES.items():

                if total_hours >= req:

                    best_role = interaction.guild.get_role(role_id)

            if best_role:
                await member.add_roles(best_role)

        # =================================================
        # UPDATE EMBED
        # =================================================

        embed = interaction.message.embeds[0]

        embed.color = discord.Color.red()

        for i, field in enumerate(embed.fields):

            if field.name == "Status":

                embed.set_field_at(
                    i,
                    name="Status",
                    value=f"🟢 Approved by {interaction.user.mention}",
                    inline=False
                )

        await interaction.message.edit(
            embed=embed,
            view=self
        )

        # =================================================
        # DM USER
        # =================================================

        if member:

            try:

                await member.send(
                    f"""
✅ Your PIREP #{self.pirep_id} was approved.

🕒 Total Hours: {total_hours}
🏅 Rank: {rank_name}
"""
                )

            except:
                pass

        await interaction.followup.send(
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
        custom_id="pirep_deny_button"
    )
    async def deny(self, interaction: discord.Interaction, button: discord.ui.Button):

        if STAFF_ROLE not in [r.id for r in interaction.user.roles]:

            return await interaction.response.send_message(
                "❌ Staff only.",
                ephemeral=True
            )

        await interaction.response.defer(ephemeral=True)

        pireps = load_json(PIREP_FILE, [])

        for p in pireps:

            if p["id"] == self.pirep_id:

                p["status"] = "Denied"

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

        await interaction.message.edit(
            embed=embed,
            view=self
        )

        await interaction.followup.send(
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
        custom_id="pirep_edit_button"
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
        label="Flight Number"
    )

    route = discord.ui.TextInput(
        label="From - To",
        placeholder="VABB - OMDB"
    )

    aircraft = discord.ui.TextInput(
        label="Aircraft"
    )

    flight_time = discord.ui.TextInput(
        label="Flight Time",
        placeholder="2h 15m"
    )

    operator = discord.ui.TextInput(
        label="Operator"
    )

    multiplier = discord.ui.TextInput(
        label="Multiplier",
        placeholder="1.0x"
    )

    comments = discord.ui.TextInput(
        label="Comments (Optional)",
        style=discord.TextStyle.paragraph,
        required=False
    )

    async def on_submit(self, interaction: discord.Interaction):

        await interaction.response.defer(ephemeral=True)

        try:

            dep, arr = [
                x.strip().upper()
                for x in self.route.value.split("-")
            ]

        except:

            return await interaction.followup.send(
                "❌ Invalid route format.\nUse: VABB - OMDB",
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
            "operator": self.operator.value,
            "multiplier": self.multiplier.value,
            "comments": self.comments.value,
            "status": "Pending"
        }

        pireps.append(data)

        save_json(PIREP_FILE, pireps)

        embed = discord.Embed(
            title=f"✈️ PIREP #{pirep_id}",
            color=discord.Color.red()
        )

        embed.add_field(
            name="Flight Number",
            value=self.flight_number.value,
            inline=True
        )

        embed.add_field(
            name="Route",
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
            value=self.operator.value,
            inline=True
        )

        embed.add_field(
            name="Multiplier",
            value=self.multiplier.value,
            inline=True
        )

        embed.add_field(
            name="Comments",
            value=self.comments.value or "None",
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

        if not log_channel:

            return await interaction.followup.send(
                "❌ PIREP log channel not found.",
                ephemeral=True
            )

        await log_channel.send(
            embed=embed,
            view=PirepButtons(
                pirep_id,
                interaction.user.id
            )
        )

        await interaction.followup.send(
            "✅ PIREP submitted successfully.",
            ephemeral=True
        )

# =========================================================
# ✈️ PANEL VIEW
# =========================================================

class PirepPanel(discord.ui.View):

    def __init__(self):

        super().__init__(timeout=None)

    @discord.ui.button(
        label="Submit PIREP",
        emoji="✈️",
        style=discord.ButtonStyle.secondary,
        custom_id="submit_pirep_panel_button"
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

        # =================================================
        # PERSISTENT VIEWS
        # =================================================

        self.bot.add_view(PirepPanel())

    # =====================================================
    # PANEL COMMAND
    # =====================================================

    @app_commands.command(
        name="pirep-panel",
        description="Send PIREP panel"
    )
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
                "Welcome to the PIREP submission center! "
                "Please submit your completed flights here for review and logging.\n\n"

                "📌 Make sure to include accurate flight details, including:\n\n"

                "- Flight Number\n"
                "- Departure & Arrival Airports\n"
                "- Aircraft Used\n"
                "- Flight Time\n"
                "- Route Information\n\n"

                "📊 Our staff team will review your PIREP as soon as possible.\n"
                "Once approved, your flight hours and statistics will be updated automatically.\n\n"

                "Thank you for flying with SGVA, and enjoy your journey in the Infinite Flight skies! ✈️"
            ),
            color=discord.Color.red()
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

        embed = discord.Embed(
            title="✈️ Your Recent PIREPs",
            color=discord.Color.red()
        )

        for p in reversed(user_pireps):

            embed.add_field(
                name=f"PIREP #{p['id']} • {p['status']}",
                value=(
                    f"📍 {p['departure']} → {p['arrival']}\n"
                    f"🛩️ {p['aircraft']}\n"
                    f"🕒 {p['flight_time']}"
                ),
                inline=False
            )

        await interaction.response.send_message(
            embed=embed,
            ephemeral=True
        )

    # =====================================================
    # 📊 STATS
    # =====================================================

    @app_commands.command(
        name="pirep-stats",
        description="View your pilot stats"
    )
    async def pirep_stats(
        self,
        interaction: discord.Interaction
    ):

        await interaction.response.defer(ephemeral=True)

        pireps = load_json(PIREP_FILE, [])

        approved = [
            p for p in pireps
            if p["user_id"] == interaction.user.id
            and p["status"] == "Approved"
        ]

        pending = [
            p for p in pireps
            if p["user_id"] == interaction.user.id
            and p["status"] == "Pending"
        ]

        denied = [
            p for p in pireps
            if p["user_id"] == interaction.user.id
            and p["status"] == "Denied"
        ]

        total_minutes = sum(
            parse_flight_time(p["flight_time"])
            for p in approved
        )

        hours = total_minutes // 60
        minutes = total_minutes % 60

        total_hours_decimal = round(total_minutes / 60, 1)

        rank_name, next_rank = get_rank(total_hours_decimal)

        embed = discord.Embed(
            title="📊 Pilot Statistics",
            color=discord.Color.red()
        )

        embed.add_field(
            name="Pilot",
            value=interaction.user.mention,
            inline=False
        )

        embed.add_field(
            name="Approved Flights",
            value=str(len(approved)),
            inline=True
        )

        embed.add_field(
            name="Pending Flights",
            value=str(len(pending)),
            inline=True
        )

        embed.add_field(
            name="Denied Flights",
            value=str(len(denied)),
            inline=True
        )

        embed.add_field(
            name="Total Hours",
            value=f"{hours}h {minutes}m",
            inline=True
        )

        embed.add_field(
            name="Current Rank",
            value=rank_name,
            inline=True
        )

        if next_rank:

            req, next_name = next_rank

            remaining = round(req - total_hours_dec

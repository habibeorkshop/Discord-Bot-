# =========================================================
# ✈️ SGVA COMPLETE ADVANCED PIREP SYSTEM
# FILE: pirep.py
# =========================================================
#
# FEATURES:
#
# ✅ PIREP PANEL
# ✅ SUBMIT PIREP BUTTON
# ✅ MODAL SYSTEM
# ✅ APPROVE / DENY / EDIT
# ✅ ADVANCED RANK SYSTEM
# ✅ AUTO ROLE PROGRESSION
# ✅ RANK PROMOTION EMBEDS
# ✅ RANKUP CHANNEL LOGS
# ✅ PIREP STATS
# ✅ PIREP LIST
# ✅ LEADERBOARD
# ✅ LOGBOOK
# ✅ JSON DATABASE
# ✅ PERSISTENT BUTTONS
# ✅ DM NOTIFICATIONS
# ✅ FAVORITE AIRCRAFT
# ✅ FAVORITE ROUTES
# ✅ AVERAGE FLIGHT TIME
#
# =========================================================

import discord
from discord.ext import commands
from discord import app_commands
import json
import os
import re
from collections import Counter

# =========================================================
# 🔧 CONFIG
# =========================================================

STAFF_ROLE = 1493559145876557955

PIREP_LOG_CHANNEL_ID = 1493812350908760065

RANKUP_CHANNEL_ID = 1501768831964811345

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
# 🏅 RANKS
# =========================================================

RANKS = [
    (0, "Cadet"),
    (5, "Junior First Officer"),
    (15, "Senior First Officer"),
    (35, "Captain"),
    (60, "Senior Captain"),
    (100, "Chief Pilot"),
    (200, "Elite Pilot")
]

# =========================================================
# 📁 DATABASE
# =========================================================

PIREP_FILE = "pireps.json"

# =========================================================
# 📁 JSON
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
# 🕒 TIME PARSER
# =========================================================

def parse_flight_time(time_str):

    time_str = time_str.lower()

    hours = 0
    minutes = 0

    h_match = re.search(r"(\d+)h", time_str)
    m_match = re.search(r"(\d+)m", time_str)

    if h_match:
        hours = int(h_match.group(1))

    if m_match:
        minutes = int(m_match.group(1))

    return (hours * 60) + minutes

def flight_hours_to_decimal(time_str):

    total_minutes = parse_flight_time(time_str)

    return round(total_minutes / 60, 1)

# =========================================================
# 🏅 GET RANK
# =========================================================

def get_rank(total_hours):

    current_rank = "Cadet"
    next_rank = None

    for req, rank in RANKS:

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
# ✅ BUTTONS
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
        custom_id="approve_pirep_btn"
    )
    async def approve(self, interaction: discord.Interaction, button: discord.ui.Button):

        if STAFF_ROLE not in [r.id for r in interaction.user.roles]:

            return await interaction.response.send_message(
                "❌ Staff only.",
                ephemeral=True
            )

        await interaction.response.defer(ephemeral=True)

        pireps = load_json(PIREP_FILE, [])

        target = None

        for p in pireps:

            if p["id"] == self.pirep_id:

                p["status"] = "Approved"
                p["reviewed_by"] = interaction.user.name
                target = p

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

        old_rank, _ = get_rank(
            max(
                total_hours - flight_hours_to_decimal(
                    target["flight_time"]
                ),
                0
            )
        )

        new_rank, _ = get_rank(total_hours)

        member = interaction.guild.get_member(
            self.pilot_id
        )

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

        embed.color = discord.Color.green()

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
        # RANKUP EMBED
        # =================================================

        if old_rank != new_rank and member:

            rank_channel = interaction.guild.get_channel(
                RANKUP_CHANNEL_ID
            )

            if rank_channel:

                promotion_embed = discord.Embed(
                    title="🏅 SGVA Rank Promotion",
                    description=(
                        f"{member.mention} has been promoted!"
                    ),
                    color=discord.Color.red()
                )

                promotion_embed.add_field(
                    name="📈 Previous Rank",
                    value=old_rank,
                    inline=True
                )

                promotion_embed.add_field(
                    name="🎖️ New Rank",
                    value=new_rank,
                    inline=True
                )

                promotion_embed.add_field(
                    name="🕒 Total Hours",
                    value=f"{total_hours} hrs",
                    inline=True
                )

                promotion_embed.add_field(
                    name="✈️ Total Flights",
                    value=str(len(approved)),
                    inline=True
                )

                promotion_embed.add_field(
                    name="🛩️ Latest Aircraft",
                    value=target["aircraft"],
                    inline=True
                )

                promotion_embed.add_field(
                    name="📍 Latest Route",
                    value=f"{target['departure']} → {target['arrival']}",
                    inline=True
                )

                promotion_embed.set_thumbnail(
                    url=member.display_avatar.url
                )

                promotion_embed.set_footer(
                    text="SGVA Rank System"
                )

                await rank_channel.send(
                    embed=promotion_embed
                )

        # =================================================
        # DM USER
        # =================================================

        if member:

            try:

                dm_embed = discord.Embed(
                    title="✅ PIREP Approved",
                    description=(
                        f"Your PIREP #{self.pirep_id} "
                        f"has been approved."
                    ),
                    color=discord.Color.red()
                )

                dm_embed.add_field(
                    name="🕒 Total Hours",
                    value=f"{total_hours} hrs"
                )

                dm_embed.add_field(
                    name="🏅 Rank",
                    value=new_rank
                )

                await member.send(embed=dm_embed)

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
        custom_id="deny_pirep_btn"
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
        custom_id="edit_pirep_btn"
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
# 📝 MODAL
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

    extra = discord.ui.TextInput(
        label="Operator | Multiplier | Comments",
        style=discord.TextStyle.paragraph,
        placeholder="SpiceJet | 1.0x | Smooth flight",
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
                "❌ Invalid route format.",
                ephemeral=True
            )

        operator = "Unknown"
        multiplier = "1.0x"
        comments = "None"

        try:

            parts = [
                x.strip()
                for x in self.extra.value.split("|")
            ]

            if len(parts) >= 1:
                operator = parts[0]

            if len(parts) >= 2:
                multiplier = parts[1]

            if len(parts) >= 3:
                comments = parts[2]

        except:
            pass

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
            color=discord.Color.red()
        )

        embed.add_field(
            name="Flight Number",
            value=self.flight_number.value
        )

        embed.add_field(
            name="Route",
            value=f"{dep} → {arr}"
        )

        embed.add_field(
            name="Aircraft",
            value=self.aircraft.value
        )

        embed.add_field(
            name="Flight Time",
            value=self.flight_time.value
        )

        embed.add_field(
            name="Operator",
            value=operator
        )

        embed.add_field(
            name="Multiplier",
            value=multiplier
        )

        embed.add_field(
            name="Comments",
            value=comments,
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
        custom_id="submit_pirep_button"
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
    # /PIREP-STATS
    # =====================================================

    @app_commands.command(
        name="pirep-stats",
        description="View your advanced pilot statistics"
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

        approved = [
            p for p in user_pireps
            if p["status"] == "Approved"
        ]

        pending = [
            p for p in user_pireps
            if p["status"] == "Pending"
        ]

        denied = [
            p for p in user_pireps
            if p["status"] == "Denied"
        ]

        total_minutes = sum(
            parse_flight_time(p["flight_time"])
            for p in approved
        )

        total_hours = round(total_minutes / 60, 1)

        hours = total_minutes // 60
        minutes = total_minutes % 60

        current_rank, next_rank = get_rank(total_hours)

        # Favorite Aircraft
        aircraft_counter = Counter(
            p["aircraft"] for p in approved
        )

        favorite_aircraft = (
            aircraft_counter.most_common(1)[0][0]
            if aircraft_counter else "N/A"
        )

        # Favorite Route
        route_counter = Counter(
            f"{p['departure']} → {p['arrival']}"
            for p in approved
        )

        favorite_route = (
            route_counter.most_common(1)[0][0]
            if route_counter else "N/A"
        )

        # Operators
        operators = set(
            p["operator"]
            for p in approved
        )

        # Average Flight Time
        avg_minutes = (
            total_minutes // len(approved)
            if approved else 0
        )

        avg_h = avg_minutes // 60
        avg_m = avg_minutes % 60

        embed = discord.Embed(
            title="📊 Advanced Pilot Statistics",
            color=discord.Color.red()
        )

        embed.add_field(
            name="✈️ Total Flights",
            value=str(len(approved)),
            inline=True
        )

        embed.add_field(
            name="🕒 Total Hours",
            value=f"{hours}h {minutes}m",
            inline=True
        )

        embed.add_field(
            name="🏅 Current Rank",
            value=current_rank,
            inline=True
        )

        embed.add_field(
            name="🟢 Approved",
            value=str(len(approved)),
            inline=True
        )

        embed.add_field(
            name="🟡 Pending",
            value=str(len(pending)),
            inline=True
        )

        embed.add_field(
            name="🔴 Denied",
            value=str(len(denied)),
            inline=True
        )

        if next_rank:

            req, next_name = next_rank

            remaining = round(req - total_hours, 1)

            embed.add_field(
                name="📈 Next Rank",
                value=next_name,
                inline=True
            )

            embed.add_field(
                name="⏳ Hours Remaining",
                value=f"{remaining} hrs",
                inline=True
            )

        embed.add_field(
            name="🛩️ Favorite Aircraft",
            value=favorite_aircraft,
            inline=True
        )

        embed.add_field(
            name="🌍 Favorite Route",
            value=favorite_route,
            inline=True
        )

        embed.add_field(
            name="🏢 Operators Used",
            value=str(len(operators)),
            inline=True
        )

        embed.add_field(
            name="📊 Average Flight Time",
            value=f"{avg_h}h {avg_m}m",
            inline=True
        )

        await interaction.response.send_message(
            embed=embed,
            ephemeral=True
        )

    # =====================================================
    # /PIREP-LIST
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
        ][-5:]

        if not user_pireps:
            return await interaction.response.send_message(
                "❌ No PIREPs found.",
                ephemeral=True
            )

        embed = discord.Embed(
            title="📋 Recent PIREPs",
            color=discord.Color.red()
        )

        for p in reversed(user_pireps):

            embed.add_field(
                name=f"✈️ {p['flight_number']}",
                value=(
                    f"📍 {p['departure']} → {p['arrival']}\n"
                    f"🛩️ {p['aircraft']}\n"
                    f"🕒 {p['flight_time']}\n"
                    f"📊 {p['status']}"
                ),
                inline=False
            )

        await interaction.response.send_message(
            embed=embed,
            ephemeral=True
        )

    # =====================================================
    # /LEADERBOARD
    # =====================================================

    @app_commands.command(
        name="leaderboard",
        description="View SGVA leaderboard"
    )
    async def leaderboard(
        self,
        interaction: discord.Interaction
    ):

        pireps = load_json(PIREP_FILE, [])

        leaderboard_data = {}

        for p in pireps:

            if p["status"] != "Approved":
                continue

            uid = p["user_id"]

            if uid not in leaderboard_data:
                leaderboard_data[uid] = {
                    "flights": 0,
                    "minutes": 0
                }

            leaderboard_data[uid]["flights"] += 1
            leaderboard_data[uid]["minutes"] += parse_flight_time(
                p["flight_time"]
            )

        sorted_users = sorted(
            leaderboard_data.items(),
            key=lambda x: x[1]["minutes"],
            reverse=True
        )[:10]

        embed = discord.Embed(
            title="🏆 SGVA Leaderboard",
            color=discord.Color.red()
        )

        position = 1

        for uid, data in sorted_users:

            member = interaction.guild.get_member(uid)

            name = member.name if member else "Unknown"

            hours = round(data["minutes"] / 60, 1)

            embed.add_field(
                name=f"#{position} • {name}",
                value=(
                    f"✈️ Flights: {data['flights']}\n"
                    f"🕒 Hours: {hours}"
                ),
                inline=False
            )

            position += 1

        await interaction.response.send_message(
            embed=embed
        )

    # =====================================================
    # /LOGBOOK
    # =====================================================

    @app_commands.command(
        name="logbook",
        description="View your pilot logbook"
    )
    async def logbook(
        self,
        interaction: discord.Interaction
    ):

        pireps = load_json(PIREP_FILE, [])

        approved = [
            p for p in pireps
            if p["user_id"] == interaction.user.id
            and p["status"] == "Approved"
        ]

        if not approved:
            return await interaction.response.send_message(
                "❌ No approved PIREPs.",
                ephemeral=True
            )

        routes = set(
            f"{p['departure']} → {p['arrival']}"
            for p in approved
        )

        aircraft = set(
            p["aircraft"]
            for p in approved
        )

        longest = max(
            approved,
            key=lambda x: parse_flight_time(x["flight_time"])
        )

        last_flight = approved[-1]
        first_flight = approved[0]

        embed = discord.Embed(
            title="📘 Pilot Logbook",
            color=discord.Color.red()
        )

        embed.add_field(
            name="🌍 Total Routes",
            value=str(len(routes)),
            inline=True
        )

        embed.add_field(
            name="🛩️ Aircraft Flown",
            value=str(len(aircraft)),
            inline=True
        )

        embed.add_field(
            name="🕒 Longest Flight",
            value=(
                f"{longest['flight_number']}\n"
                f"{longest['flight_time']}"
            ),
            inline=False
        )

        embed.add_field(
            name="📍 Last Flight",
            value=(
                f"{last_flight['departure']} → "
                f"{last_flight['arrival']}"
            ),
            inline=False
        )

        embed.add_field(
            name="📅 First Flight",
            value=first_flight["created_at"],
            inline=False
        )

        await interaction.response.send_message(
            embed=embed,
            ephemeral=True
        )

    # =====================================================
    # PANEL
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

        "📌 Make sure to include accurate flight details:\n\n"

        "• Flight Number\n"
        "• Departure & Arrival Airports\n"
        "• Aircraft Used\n"
        "• Flight Time\n"
        "• Route Information\n\n"

        "📊 Staff will review your PIREP soon.\n"
        "Approved PIREPs update your statistics automatically.\n\n"

        "Thank you for flying with SGVA ✈️"
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

# =========================================================
# 🔌 LOAD
# =========================================================

async def setup(bot):

    await bot.add_cog(Pirep(bot))

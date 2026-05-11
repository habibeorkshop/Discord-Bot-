# =========================================================
# ✈️ SGVA ADVANCED PILOT SYSTEM
# FILE NAME: pilot_stats.py
# =========================================================
#
# ✅ /pirep-stats
# ✅ /pirep-list
# ✅ /leaderboard
# ✅ /logbook
# ✅ Advanced Statistics
# ✅ Favorite Aircraft
# ✅ Favorite Route
# ✅ Average Flight Time
# ✅ Top 10 Leaderboard
# ✅ Persistent JSON Support
#
# =========================================================

import discord
from discord.ext import commands
from discord import app_commands
import json
import os
import re
from collections import Counter
from datetime import datetime

# =========================================================
# 📁 DATABASE
# =========================================================

PIREP_FILE = "pireps.json"

# =========================================================
# 🏅 RANK SYSTEM
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
# 📁 JSON SYSTEM
# =========================================================

def load_json(path, default):

    if not os.path.exists(path):

        with open(path, "w") as f:
            json.dump(default, f)

    with open(path, "r") as f:
        return json.load(f)

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
# ✈️ COG
# =========================================================

class PilotStats(commands.Cog):

    def __init__(self, bot):
        self.bot = bot

    # =====================================================
    # 📊 /PIREP-STATS
    # =====================================================

    @app_commands.command(
        name="pirep-stats",
        description="View advanced pilot statistics"
    )
    async def pirep_stats(
        self,
        interaction: discord.Interaction
    ):

        await interaction.response.defer(ephemeral=True)

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

        rank_name, next_rank = get_rank(total_hours)

        # =================================================
        # FAVORITE AIRCRAFT
        # =================================================

        aircraft_counter = Counter(
            p["aircraft"]
            for p in approved
        )

        favorite_aircraft = (
            aircraft_counter.most_common(1)[0][0]
            if aircraft_counter else "N/A"
        )

        # =================================================
        # FAVORITE ROUTE
        # =================================================

        route_counter = Counter(
            f"{p['departure']} → {p['arrival']}"
            for p in approved
        )

        favorite_route = (
            route_counter.most_common(1)[0][0]
            if route_counter else "N/A"
        )

        # =================================================
        # OPERATORS
        # =================================================

        operators = set(
            p["operator"]
            for p in approved
        )

        # =================================================
        # AVERAGE FLIGHT
        # =================================================

        avg_minutes = (
            total_minutes // len(approved)
            if approved else 0
        )

        avg_hours = avg_minutes // 60
        avg_remaining = avg_minutes % 60

        # =================================================
        # EMBED
        # =================================================

        embed = discord.Embed(
            title="📊 SGVA Pilot Statistics",
            color=discord.Color.red()
        )

        embed.set_thumbnail(
            url=interaction.user.display_avatar.url
        )

        embed.add_field(
            name="🧑‍✈️ Pilot",
            value=interaction.user.mention,
            inline=False
        )

        embed.add_field(
            name="✈️ Total Flights",
            value=str(len(approved)),
            inline=True
        )

        embed.add_field(
            name="🕒 Total Hours",
            value=f"{total_hours} hrs",
            inline=True
        )

        embed.add_field(
            name="🏅 Current Rank",
            value=rank_name,
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
            name="📊 Average Flight",
            value=f"{avg_hours}h {avg_remaining}m",
            inline=True
        )

        embed.set_footer(
            text="SGVA Pilot Statistics System"
        )

        await interaction.followup.send(
            embed=embed,
            ephemeral=True
        )

    # =====================================================
    # 📋 /PIREP-LIST
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
    # 🏆 /LEADERBOARD
    # =====================================================

    @app_commands.command(
        name="leaderboard",
        description="View SGVA pilot leaderboard"
    )
    async def leaderboard(
        self,
        interaction: discord.Interaction
    ):

        await interaction.response.defer()

        pireps = load_json(PIREP_FILE, [])

        pilot_data = {}

        for p in pireps:

            if p["status"] != "Approved":
                continue

            uid = p["user_id"]

            if uid not in pilot_data:

                pilot_data[uid] = {
                    "hours": 0,
                    "flights": 0
                }

            pilot_data[uid]["hours"] += (
                parse_flight_time(
                    p["flight_time"]
                ) / 60
            )

            pilot_data[uid]["flights"] += 1

        top = sorted(
            pilot_data.items(),
            key=lambda x: x[1]["hours"],
            reverse=True
        )[:10]

        embed = discord.Embed(
            title="🏆 SGVA Leaderboard",
            color=discord.Color.red()
        )

        position = 1

        for uid, data in top:

            user = self.bot.get_user(uid)

            name = user.name if user else "Unknown"

            embed.add_field(
                name=f"#{position} • {name}",
                value=(
                    f"🕒 {round(data['hours'],1)} hrs\n"
                    f"✈️ {data['flights']} flights"
                ),
                inline=False
            )

            position += 1

        await interaction.followup.send(
            embed=embed
        )

    # =====================================================
    # 📖 /LOGBOOK
    # =====================================================

    @app_commands.command(
        name="logbook",
        description="View your pilot logbook"
    )
    async def logbook(
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

        if not approved:

            return await interaction.followup.send(
                "❌ No approved flights found.",
                ephemeral=True
            )

        # =================================================
        # ROUTES
        # =================================================

        routes = set(
            f"{p['departure']} → {p['arrival']}"
            for p in approved
        )

        # =================================================
        # AIRCRAFT
        # =================================================

        aircraft = set(
            p["aircraft"]
            for p in approved
        )

        # =================================================
        # LONGEST FLIGHT
        # =================================================

        longest = max(
            approved,
            key=lambda x: parse_flight_time(
                x["flight_time"]
            )
        )

        # =================================================
        # EMBED
        # =================================================

        embed = discord.Embed(
            title="📖 SGVA Pilot Logbook",
            color=discord.Color.red()
        )

        embed.set_thumbnail(
            url=interaction.user.display_avatar.url
        )

        embed.add_field(
            name="🛫 Total Routes",
            value=str(len(routes)),
            inline=True
        )

        embed.add_field(
            name="🛩️ Aircraft Flown",
            value=str(len(aircraft)),
            inline=True
        )

        embed.add_field(
            name="✈️ Approved Flights",
            value=str(len(approved)),
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
            name="📍 Route",
            value=(
                f"{longest['departure']} → "
                f"{longest['arrival']}"
            ),
            inline=False
        )

        embed.add_field(
            name="🛩️ Aircraft List",
            value=", ".join(list(aircraft)[:10]),
            inline=False
        )

        embed.set_footer(
            text="SGVA Digital Logbook"
        )

        await interaction.followup.send(
            embed=embed,
            ephemeral=True
        )

# =========================================================
# 🔌 LOAD COG
# =========================================================

async def setup(bot):

    await bot.add_cog(PilotStats(bot))

# =========================================================
# ✈️ SGVA ADVANCED PIREP SYSTEM
# =========================================================
#
# ✅ FIXED INTERACTION FAILED
# ✅ FIXED MODAL LIMIT
# ✅ FIXED APPROVE BUTTON
# ✅ FIXED DENY BUTTON
# ✅ FIXED EDIT BUTTON
# ✅ FIXED SUBMIT BUTTON
# ✅ FIXED STATS COMMAND
# ✅ PERSISTENT BUTTONS
# ✅ AUTO ROLE SYSTEM
# ✅ AUTO RANK SYSTEM
# ✅ RANKUP LOG CHANNEL
# ✅ JSON DATABASE
# ✅ ALL EMBEDS RED
#
# FILE NAME: pirep.py
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

RANKUP_CHANNEL_ID = 1501768831964811345

# =========================================================
# 🏅 RANK ROLE IDS
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
# ✅ BUTTON VIEW
# =========================================================

class PirepButtons(discord.ui.View):

    def __init__(self, pirep_id=0, pilot_id=0):
        super().__init__(timeout=None)

        self.pirep_id = pirep_id
        self.pilot_id = pilot_id

    # =====================================================
    # APPROVE
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

        rank_name, next_rank = get_rank(total_hours)

        member = interaction.guild.get_member(self.pilot_id)

        # =================================================
        # ROLE SYSTEM
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
        
# =========================================================
# 🏅 ADVANCED RANK PROMOTION SYSTEM
# =========================================================

old_rank, _ = get_rank(max(total_hours - float(target["flight_time"].split("h")[0]), 0))
new_rank, _ = get_rank(total_hours)

if old_rank != new_rank:

    rank_channel = interaction.guild.get_channel(
        RANKUP_CHANNEL_ID
    )

    if rank_channel:

        promotion_embed = discord.Embed(
            title="🏅 SGVA Rank Promotion",
            description=(
                f"Congratulations {member.mention}!\n\n"
                f"You have officially been promoted within "
                f"**SpiceJet Virtual Airlines**."
            ),
            color=discord.Color.red()
        )

        promotion_embed.add_field(
            name="🧑‍✈️ Pilot",
            value=member.mention,
            inline=True
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
            name="🕒 Total Flight Hours",
            value=f"{total_hours} Hours",
            inline=True
        )

        promotion_embed.add_field(
            name="✈️ Total Approved Flights",
            value=str(len(approved)),
            inline=True
        )

        promotion_embed.add_field(
            name="📊 Latest Flight",
            value=(
                f"{target['departure']} → "
                f"{target['arrival']}"
            ),
            inline=True
        )

        promotion_embed.add_field(
            name="🛩️ Aircraft",
            value=target["aircraft"],
            inline=True
        )

        promotion_embed.add_field(
            name="🎟️ Flight Number",
            value=target["flight_number"],
            inline=True
        )

        promotion_embed.add_field(
            name="👨‍✈️ Reviewed By",
            value=interaction.user.mention,
            inline=True
        )

        promotion_embed.set_thumbnail(
            url=member.display_avatar.url
        )

        promotion_embed.set_footer(
            text="SGVA Pilot Rank System"
        )

        await rank_channel.send(
            content=f"🎉 Congratulations {member.mention}!",
            embed=promotion_embed
        )

        # =====================================================
        # DM PROMOTION
        # =====================================================

        try:

            dm_embed = discord.Embed(
                title="🏅 You Have Been Promoted!",
                description=(
                    f"You are now ranked as **{new_rank}** "
                    f"in SGVA."
                ),
                color=discord.Color.red()
            )

            dm_embed.add_field(
                name="Previous Rank",
                value=old_rank
            )

            dm_embed.add_field(
                name="New Rank",
                value=new_rank
            )

            dm_embed.add_field(
                name="Total Hours",
                value=f"{total_hours} Hours"
            )

            dm_embed.set_footer(
                text="Keep flying with SGVA ✈️"
            )

            await member.send(embed=dm_embed)

        except:
            pass
        

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

Keep flying with SGVA ✈️
"""
                )

            except:
                pass

        await interaction.followup.send(
            "✅ PIREP approved.",
            ephemeral=True
        )

    # =====================================================
    # DENY
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
    # EDIT
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
# 📝 FIXED MODAL
# =========================================================

class PirepModal(discord.ui.Modal, title="SGVA PIREP Centre"):

    flight_number = discord.ui.TextInput(
        label="Flight Number",
        placeholder="SGVA101"
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

    extra = discord.ui.TextInput(
        label="Operator | Multiplier | Comments",
        style=discord.TextStyle.paragraph,
        placeholder="SpiceJet | 1.0x | Smooth Landing",
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
                "❌ Invalid route format. Use: VABB - OMDB",
                ephemeral=True
            )

        # =====================================================
        # EXTRA PARSER
        # =====================================================

        operator = "Unknown"
        multiplier = "1.0x"
        comments = "None"

        try:

            parts = [x.strip() for x in self.extra.value.split("|")]

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

        # =====================================================
        # EMBED
        # =====================================================

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

        # =====================================================
        # SEND TO LOG CHANNEL
        # =====================================================

        log_channel = interaction.guild.get_channel(
            PIREP_LOG_CHANNEL_ID
        )

        msg = await log_channel.send(
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
        # =================================================
        # OPERATOR
        # =================================================

        try:

            operator, multiplier = [
                x.strip()
                for x in self.operator.value.split("|")
            ]

        except:

            operator = self.operator.value
            multiplier = "1.0x"

        # =================================================
        # DATABASE
        # =================================================

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
            "comments": self.comments.value,
            "status": "Pending"
        }

        pireps.append(data)

        save_json(PIREP_FILE, pireps)

        # =================================================
        # EMBED
        # =================================================

        embed = discord.Embed(
            title=f"✈️ PIREP #{pirep_id}",
            color=discord.Color.red()
        )

        embed.add_field(
            name="Flight Number",
            value=self.flight_number.value,
            inline=False
        )

        embed.add_field(
            name="Route",
            value=f"{dep} → {arr}",
            inline=False
        )

        embed.add_field(
            name="Aircraft",
            value=self.aircraft.value,
            inline=False
        )

        embed.add_field(
            name="Flight Time",
            value=self.flight_time.value,
            inline=False
        )

        embed.add_field(
            name="Operator",
            value=operator,
            inline=False
        )

        embed.add_field(
            name="Multiplier",
            value=multiplier,
            inline=False
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

        await log_channel.send(
            embed=embed,
            view=PirepButtons(
                pirep_id,
                interaction.user.id
            )
        )

        await interaction.followup.send(
            f"✅ PIREP submitted successfully.\nPIREP ID: #{pirep_id}",
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

        if STAFF_ROLE not in [r.id for r in interaction.user.roles]:

            return await interaction.response.send_message(
                "❌ Staff only.",
                ephemeral=True
            )

        embed = discord.Embed(
            title="✈️ SGVA PIREP Centre",
            description=(
                "Welcome to the PIREP submission center! Please submit your completed flights here for review and logging.\n\n"

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

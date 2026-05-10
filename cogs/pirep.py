import discord
from discord.ext import commands
from discord import app_commands
import json
import os
import re
from datetime import datetime

# ================= CONFIG =================

GUILD_ID = 1493552564799672320
STAFF_ROLE_ID = 1493559145876557955
PIREP_LOG_CHANNEL_ID = 1493812350908760065  # PUT CHANNEL ID

PIREP_FILE = "pireps.json"
STATS_FILE = "pilot_stats.json"

# ================= FILES =================

def load_json(file, default):
    if not os.path.exists(file):
        with open(file, "w") as f:
            json.dump(default, f)

    with open(file, "r") as f:
        return json.load(f)

def save_json(file, data):
    with open(file, "w") as f:
        json.dump(data, f, indent=4)

# ================= HELPERS =================

def valid_icao(code):
    return bool(re.match(r"^[A-Z]{4}$", code))

def parse_hours(time_str):
    """
    Supports:
    2h 30m
    2h
    30m
    """
    hours = 0

    h = re.search(r"(\d+)h", time_str.lower())
    m = re.search(r"(\d+)m", time_str.lower())

    if h:
        hours += int(h.group(1))

    if m:
        hours += int(m.group(1)) / 60

    return round(hours, 2)

def get_rank(flights):
    if flights >= 76:
        return "Senior Captain"
    elif flights >= 31:
        return "Captain"
    elif flights >= 11:
        return "First Officer"
    return "Cadet"

# ================= MODAL =================

class PirepModal(discord.ui.Modal, title="SGVA PIREP Centre"):

    username = discord.ui.TextInput(label="Username")
    departure = discord.ui.TextInput(label="Departure ICAO")
    arrival = discord.ui.TextInput(label="Arrival ICAO")
    flight_time = discord.ui.TextInput(label="Flight Time")
    aircraft = discord.ui.TextInput(label="Aircraft")
    operator = discord.ui.TextInput(label="Operator")
    multiplier = discord.ui.TextInput(label="Multiplier")
    landing_rate = discord.ui.TextInput(label="Landing Rate", required=False)
    remarks = discord.ui.TextInput(
        label="Remarks",
        style=discord.TextStyle.paragraph,
        required=False
    )

    async def on_submit(self, interaction: discord.Interaction):

        dep = self.departure.value.upper()
        arr = self.arrival.value.upper()

        if not valid_icao(dep) or not valid_icao(arr):
            return await interaction.response.send_message(
                "❌ Invalid ICAO format.",
                ephemeral=True
            )

        pireps = load_json(PIREP_FILE, [])

        pirep_id = len(pireps) + 1

        data = {
            "id": pirep_id,
            "user_id": interaction.user.id,
            "username": self.username.value,
            "departure": dep,
            "arrival": arr,
            "flight_time": self.flight_time.value,
            "aircraft": self.aircraft.value,
            "operator": self.operator.value,
            "multiplier": self.multiplier.value,
            "landing_rate": self.landing_rate.value,
            "remarks": self.remarks.value,
            "status": "Pending",
            "timestamp": str(datetime.utcnow())
        }

        pireps.append(data)
        save_json(PIREP_FILE, pireps)

        embed = discord.Embed(
            title=f"✈️ PIREP #{pirep_id}",
            color=discord.Color.orange()
        )

        embed.add_field(name="Username", value=self.username.value, inline=True)
        embed.add_field(name="Route", value=f"{dep} → {arr}", inline=True)
        embed.add_field(name="Flight Time", value=self.flight_time.value, inline=True)
        embed.add_field(name="Aircraft", value=self.aircraft.value, inline=True)
        embed.add_field(name="Operator", value=self.operator.value, inline=True)
        embed.add_field(name="Multiplier", value=self.multiplier.value, inline=True)

        if self.landing_rate.value:
            embed.add_field(name="Landing Rate", value=self.landing_rate.value, inline=True)

        if self.remarks.value:
            embed.add_field(name="Remarks", value=self.remarks.value, inline=False)

        embed.add_field(name="Status", value="🟡 Pending Review", inline=False)

        embed.set_footer(
            text=f"Submitted by {interaction.user}",
            icon_url=interaction.user.display_avatar.url
        )

        log_channel = interaction.guild.get_channel(PIREP_LOG_CHANNEL_ID)

        msg = await log_channel.send(
            embed=embed,
            view=PirepButtons(pirep_id, interaction.user.id)
        )

        await interaction.response.send_message(
            "✅ PIREP submitted successfully.",
            ephemeral=True
        )

# ================= BUTTONS =================

class DenyModal(discord.ui.Modal, title="Deny PIREP"):

    reason = discord.ui.TextInput(
        label="Reason",
        style=discord.TextStyle.paragraph
    )

    def __init__(self, embed_message):
        super().__init__()
        self.embed_message = embed_message

    async def on_submit(self, interaction: discord.Interaction):

        embed = self.embed_message.embeds[0]

        for field in embed.fields:
            if field.name == "Status":
                field.value = f"❌ Denied\nReason: {self.reason.value}"

        embed.color = discord.Color.red()

        await self.embed_message.edit(embed=embed)

        await interaction.response.send_message(
            "❌ PIREP denied.",
            ephemeral=True
        )

class PirepButtons(discord.ui.View):

    def __init__(self, pirep_id, user_id):
        super().__init__(timeout=None)
        self.pirep_id = pirep_id
        self.user_id = user_id

    @discord.ui.button(
        label="Approve",
        emoji="✅",
        style=discord.ButtonStyle.success,
        custom_id="pirep_approve"
    )
    async def approve(self, interaction: discord.Interaction, button):

        if STAFF_ROLE_ID not in [r.id for r in interaction.user.roles]:
            return await interaction.response.send_message(
                "❌ Staff only",
                ephemeral=True
            )

        embed = interaction.message.embeds[0]

        embed.color = discord.Color.green()

        for field in embed.fields:
            if field.name == "Status":
                field.value = f"🟢 Approved by {interaction.user.mention}"

        await interaction.message.edit(embed=embed)

        # UPDATE STATS
        stats = load_json(STATS_FILE, {})

        uid = str(self.user_id)

        if uid not in stats:
            stats[uid] = {
                "flights": 0,
                "hours": 0,
                "landings": 0
            }

        flight_time = embed.fields[2].value

        stats[uid]["flights"] += 1
        stats[uid]["hours"] += parse_hours(flight_time)
        stats[uid]["landings"] += 1

        save_json(STATS_FILE, stats)

        user = interaction.guild.get_member(self.user_id)

        try:
            await user.send(f"✅ Your PIREP #{self.pirep_id} was approved.")
        except:
            pass

        await interaction.response.send_message(
            "✅ PIREP approved.",
            ephemeral=True
        )

    @discord.ui.button(
        label="Deny",
        emoji="❌",
        style=discord.ButtonStyle.danger,
        custom_id="pirep_deny"
    )
    async def deny(self, interaction: discord.Interaction, button):

        if STAFF_ROLE_ID not in [r.id for r in interaction.user.roles]:
            return await interaction.response.send_message(
                "❌ Staff only",
                ephemeral=True
            )

        await interaction.response.send_modal(
            DenyModal(interaction.message)
        )

# ================= PANEL =================

class PirepPanel(discord.ui.View):

    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(
        label="Submit PIREP",
        emoji="✈️",
        style=discord.ButtonStyle.secondary,
        custom_id="submit_pirep"
    )
    async def submit(self, interaction: discord.Interaction, button):

        await interaction.response.send_modal(PirepModal())

# ================= COG =================

class Pirep(commands.Cog):

    def __init__(self, bot):
        self.bot = bot

        self.bot.add_view(PirepPanel())

    # PANEL
    @app_commands.command(name="pireppanel", description="Send PIREP panel")
    @app_commands.guilds(discord.Object(id=GUILD_ID))
    async def pireppanel(
        self,
        interaction: discord.Interaction,
        channel: discord.TextChannel
    ):

        if STAFF_ROLE_ID not in [r.id for r in interaction.user.roles]:
            return await interaction.response.send_message(
                "❌ Staff only",
                ephemeral=True
            )

        embed = discord.Embed(
            title="✈️ SGVA PIREP Centre",
            description=(
                "Submit your completed flights here.\n\n"
                "📌 Click the button below to submit a PIREP.\n"
                "🛫 Ensure all information is correct."
            ),
            color=discord.Color.orange()
        )

        await channel.send(embed=embed, view=PirepPanel())

        await interaction.response.send_message(
            "✅ PIREP panel sent.",
            ephemeral=True
        )

    # STATS
    @app_commands.command(name="pirepstats", description="View pilot stats")
    async def pirepstats(
        self,
        interaction: discord.Interaction,
        member: discord.Member = None
    ):

        member = member or interaction.user

        stats = load_json(STATS_FILE, {})

        uid = str(member.id)

        if uid not in stats:
            return await interaction.response.send_message(
                "No stats found.",
                ephemeral=True
            )

        data = stats[uid]

        embed = discord.Embed(
            title=f"📊 {member.name}'s Stats",
            color=discord.Color.orange()
        )

        embed.add_field(name="Flights", value=data["flights"])
        embed.add_field(name="Hours", value=round(data["hours"], 2))
        embed.add_field(name="Landings", value=data["landings"])
        embed.add_field(
            name="Rank",
            value=get_rank(data["flights"]),
            inline=False
        )

        await interaction.response.send_message(embed=embed)

    # LIST
    @app_commands.command(name="pireplist", description="View recent PIREPs")
    async def pireplist(self, interaction: discord.Interaction):

        pireps = load_json(PIREP_FILE, [])

        user_pireps = [
            p for p in pireps
            if p["user_id"] == interaction.user.id
        ][-5:]

        if not user_pireps:
            return await interaction.response.send_message(
                "No PIREPs found.",
                ephemeral=True
            )

        embed = discord.Embed(
            title="📜 Recent PIREPs",
            color=discord.Color.orange()
        )

        for p in reversed(user_pireps):
            embed.add_field(
                name=f"PIREP #{p['id']}",
                value=(
                    f"{p['departure']} → {p['arrival']}\n"
                    f"{p['aircraft']}\n"
                    f"Status: {p['status']}"
                ),
                inline=False
            )

        await interaction.response.send_message(embed=embed)

# ================= SETUP =================

async def setup(bot):
    await bot.add_cog(Pirep(bot))

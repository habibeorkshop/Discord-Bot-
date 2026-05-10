import discord
from discord.ext import commands
from discord import app_commands
import sqlite3
from datetime import datetime

# ================= CONFIG =================

GUILD_ID = 1493552564799672320

STAFF_ROLE_ID = 1493559145876557955

PENDING_CHANNEL_ID = 1493554353263480893
APPROVED_CHANNEL_ID = 1493554353263480893

DATABASE = "pirep.db"

# ================= DATABASE =================

conn = sqlite3.connect(DATABASE)
cursor = conn.cursor()

cursor.execute("""
CREATE TABLE IF NOT EXISTS pireps (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER,
    username TEXT,
    flight_number TEXT,
    aircraft TEXT,
    departure TEXT,
    arrival TEXT,
    route TEXT,
    flight_time TEXT,
    landing_rate TEXT,
    status TEXT,
    created_at TEXT
)
""")

conn.commit()

# ================= PIREP MODAL =================

class PirepModal(discord.ui.Modal, title="File PIREP"):

    flight_number = discord.ui.TextInput(
        label="Flight Number",
        placeholder="SJ101"
    )

    aircraft = discord.ui.TextInput(
        label="Aircraft",
        placeholder="B737 MAX 8"
    )

    departure = discord.ui.TextInput(
        label="Departure ICAO",
        placeholder="VABB"
    )

    arrival = discord.ui.TextInput(
        label="Arrival ICAO",
        placeholder="VIDP"
    )

    route = discord.ui.TextInput(
        label="Route",
        placeholder="SID DCT STAR",
        required=False
    )

    flight_time = discord.ui.TextInput(
        label="Flight Time",
        placeholder="2h 10m"
    )

    landing_rate = discord.ui.TextInput(
        label="Landing Rate",
        placeholder="-145 fpm"
    )

    async def on_submit(self, interaction: discord.Interaction):

        cursor.execute("""
        INSERT INTO pireps (
            user_id,
            username,
            flight_number,
            aircraft,
            departure,
            arrival,
            route,
            flight_time,
            landing_rate,
            status,
            created_at
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            interaction.user.id,
            str(interaction.user),
            self.flight_number.value,
            self.aircraft.value,
            self.departure.value,
            self.arrival.value,
            self.route.value,
            self.flight_time.value,
            self.landing_rate.value,
            "Pending",
            str(datetime.utcnow())
        ))

        conn.commit()

        embed = discord.Embed(
            title="🛫 New PIREP Submitted",
            color=discord.Color.orange(),
            timestamp=datetime.utcnow()
        )

        embed.add_field(
            name="👨‍✈️ Pilot",
            value=interaction.user.mention,
            inline=False
        )

        embed.add_field(
            name="✈️ Flight",
            value=self.flight_number.value
        )

        embed.add_field(
            name="🛩️ Aircraft",
            value=self.aircraft.value
        )

        embed.add_field(
            name="🛫 Departure",
            value=self.departure.value
        )

        embed.add_field(
            name="🛬 Arrival",
            value=self.arrival.value
        )

        embed.add_field(
            name="⏱️ Flight Time",
            value=self.flight_time.value
        )

        embed.add_field(
            name="📉 Landing Rate",
            value=self.landing_rate.value
        )

        embed.add_field(
            name="🗺️ Route",
            value=self.route.value or "N/A",
            inline=False
        )

        embed.add_field(
            name="📌 Status",
            value="🟡 Pending Review",
            inline=False
        )

        embed.set_footer(
            text="SpiceJet Virtual PIREP System",
            icon_url=interaction.guild.icon.url if interaction.guild.icon else None
        )

        channel = interaction.guild.get_channel(PENDING_CHANNEL_ID)

        await channel.send(
            content=f"<@&{STAFF_ROLE_ID}>",
            embed=embed,
            view=PirepButtons()
        )

        await interaction.response.send_message(
            "✅ Your PIREP has been submitted.",
            ephemeral=True
        )

# ================= APPROVE / DENY =================

class PirepButtons(discord.ui.View):

    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(
        label="Approve",
        emoji="✅",
        style=discord.ButtonStyle.success,
        custom_id="pirep_approve"
    )
    async def approve(
        self,
        interaction: discord.Interaction,
        button: discord.ui.Button
    ):

        if STAFF_ROLE_ID not in [r.id for r in interaction.user.roles]:
            return await interaction.response.send_message(
                "❌ Staff only.",
                ephemeral=True
            )

        embed = interaction.message.embeds[0]

        embed.color = discord.Color.green()

        for i, field in enumerate(embed.fields):

            if field.name == "📌 Status":

                embed.set_field_at(
                    i,
                    name="📌 Status",
                    value=f"✅ Approved by {interaction.user.mention}",
                    inline=False
                )

        await interaction.message.edit(
            embed=embed,
            view=None
        )

        approved_channel = interaction.guild.get_channel(APPROVED_CHANNEL_ID)

        await approved_channel.send(embed=embed)

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
    async def deny(
        self,
        interaction: discord.Interaction,
        button: discord.ui.Button
    ):

        if STAFF_ROLE_ID not in [r.id for r in interaction.user.roles]:
            return await interaction.response.send_message(
                "❌ Staff only.",
                ephemeral=True
            )

        embed = interaction.message.embeds[0]

        embed.color = discord.Color.red()

        for i, field in enumerate(embed.fields):

            if field.name == "📌 Status":

                embed.set_field_at(
                    i,
                    name="📌 Status",
                    value=f"❌ Denied by {interaction.user.mention}",
                    inline=False
                )

        await interaction.message.edit(
            embed=embed,
            view=None
        )

        await interaction.response.send_message(
            "❌ PIREP denied.",
            ephemeral=True
        )

# ================= PANEL BUTTONS =================

class PirepPanelButtons(discord.ui.View):

    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(
        label="File PIREP",
        emoji="🛫",
        style=discord.ButtonStyle.secondary,
        custom_id="file_pirep"
    )
    async def file_pirep(
        self,
        interaction: discord.Interaction,
        button: discord.ui.Button
    ):

        await interaction.response.send_modal(
            PirepModal()
        )

    @discord.ui.button(
        label="My Stats",
        emoji="📊",
        style=discord.ButtonStyle.secondary,
        custom_id="pirep_stats"
    )
    async def stats(
        self,
        interaction: discord.Interaction,
        button: discord.ui.Button
    ):

        cursor.execute("""
        SELECT COUNT(*)
        FROM pireps
        WHERE user_id = ?
        """, (interaction.user.id,))

        total = cursor.fetchone()[0]

        cursor.execute("""
        SELECT COUNT(*)
        FROM pireps
        WHERE user_id = ?
        AND status = 'Pending'
        """, (interaction.user.id,))

        pending = cursor.fetchone()[0]

        embed = discord.Embed(
            title=f"📊 {interaction.user.display_name} Stats",
            color=discord.Color.orange()
        )

        embed.add_field(name="Total Flights", value=total)
        embed.add_field(name="Pending", value=pending)

        await interaction.response.send_message(
            embed=embed,
            ephemeral=True
        )

    @discord.ui.button(
        label="Leaderboard",
        emoji="🏆",
        style=discord.ButtonStyle.secondary,
        custom_id="pirep_leaderboard"
    )
    async def leaderboard(
        self,
        interaction: discord.Interaction,
        button: discord.ui.Button
    ):

        cursor.execute("""
        SELECT username, COUNT(*)
        FROM pireps
        GROUP BY username
        ORDER BY COUNT(*) DESC
        LIMIT 10
        """)

        results = cursor.fetchall()

        embed = discord.Embed(
            title="🏆 Top Pilots",
            color=discord.Color.gold()
        )

        if not results:
            embed.description = "No PIREPs filed yet."

        else:

            desc = ""

            for i, row in enumerate(results, start=1):

                desc += f"**{i}.** {row[0]} — `{row[1]} flights`\n"

            embed.description = desc

        await interaction.response.send_message(
            embed=embed,
            ephemeral=True
        )

# ================= COG =================

class Pirep(commands.Cog):

    def __init__(self, bot):
        self.bot = bot

        self.bot.add_view(PirepPanelButtons())
        self.bot.add_view(PirepButtons())

    @app_commands.command(
        name="pireppanel",
        description="Send PIREP panel"
    )
    @app_commands.guilds(
        discord.Object(id=GUILD_ID)
    )
    async def pireppanel(
        self,
        interaction: discord.Interaction,
        channel: discord.TextChannel
    ):

        if STAFF_ROLE_ID not in [r.id for r in interaction.user.roles]:
            return await interaction.response.send_message(
                "❌ Staff only.",
                ephemeral=True
            )

        embed = discord.Embed(
            title="🛫 SpiceJet Virtual PIREP Center",
            description=(
                "Welcome to the official PIREP system.\n\n"
                "Use the buttons below to:\n"
                "• File your flight report\n"
                "• View your pilot stats\n"
                "• Check leaderboard rankings\n\n"
                "Please ensure all reports are accurate."
            ),
            color=discord.Color.orange()
        )

        embed.set_footer(
            text="SpiceJet Virtual Airlines"
        )

        await channel.send(
            embed=embed,
            view=PirepPanelButtons()
        )

        await interaction.response.send_message(
            "✅ PIREP panel sent.",
            ephemeral=True
        )

# ================= SETUP =================

async def setup(bot):
    await bot.add_cog(Pirep(bot))

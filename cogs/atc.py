import discord
from discord.ext import commands
from discord import app_commands
import aiohttp
import os

# 🔧 CONFIG
IF_API_KEY = os.getenv("IF_API_KEY")
GUILD_ID = 1493552564799672320
BASE_URL = "https://api.infiniteflight.com/public/v2"


# ================= AIRPORT SELECT =================

class AirportSelect(discord.ui.Select):
    def __init__(self, airports, session_id):
        self.airports = airports
        self.session_id = session_id

        options = [
            discord.SelectOption(label=icao, description=f"{len(v)} ATC online")
            for icao, v in list(airports.items())[:25]
        ]

        super().__init__(
            placeholder="Select airport...",
            options=options,
            custom_id="atc_airport_select_expert"
        )

    async def callback(self, interaction: discord.Interaction):
        await interaction.response.defer()

        airport = self.values[0]
        atc_units = self.airports.get(airport, [])

        # ================= CONTROLLERS =================
        controllers = []
        for atc in atc_units:
            name = atc.get("username", "Unknown")
            freq = atc.get("frequency", "N/A")
            controllers.append(f"{name} ({freq})")

        controller_text = "\n".join(controllers)[:1000] or "None"

        # ================= TRAFFIC =================
        inbound = 0
        outbound = 0

        async with aiohttp.ClientSession() as session:
            async with session.get(
                f"{BASE_URL}/sessions/{self.session_id}/flights?apikey={IF_API_KEY}"
            ) as resp:
                flights = await resp.json()

        for f in flights.get("result", []):
            if f.get("arrivalAirportIcao") == airport:
                inbound += 1
            if f.get("departureAirportIcao") == airport:
                outbound += 1

        # ================= EMBED =================
        embed = discord.Embed(
            title=f"📡 ATC Active — {airport}",
            color=discord.Color.green()
        )

        embed.add_field(
            name="👨‍✈️ Controllers",
            value=controller_text,
            inline=False
        )

        embed.add_field(
            name="📊 Traffic",
            value=f"🛬 Inbound: {inbound}\n🛫 Outbound: {outbound}",
            inline=False
        )

        embed.add_field(
            name="🌐 Server",
            value="Expert",
            inline=True
        )

        await interaction.followup.send(embed=embed)


# ================= VIEW =================

class ATCView(discord.ui.View):
    def __init__(self, airports, session_id):
        super().__init__(timeout=120)
        self.add_item(AirportSelect(airports, session_id))


# ================= COG =================

class ATC(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="atc", description="Show active ATC airports (Expert Server)")
    @app_commands.guilds(discord.Object(id=GUILD_ID))
    async def atc(self, interaction: discord.Interaction):

        if not IF_API_KEY:
            return await interaction.response.send_message(
                "❌ API key missing",
                ephemeral=True
            )

        await interaction.response.defer(ephemeral=True)

        # ================= GET EXPERT SESSION =================
        async with aiohttp.ClientSession() as session:
            async with session.get(f"{BASE_URL}/sessions?apikey={IF_API_KEY}") as resp:
                sessions = await resp.json()

        session_id = None
        for s in sessions.get("result", []):
            if "expert" in s.get("name", "").lower():
                session_id = s.get("id")
                break

        if not session_id:
            return await interaction.followup.send("❌ Expert server not found")

        # ================= GET ATC =================
        async with aiohttp.ClientSession() as session:
            async with session.get(
                f"{BASE_URL}/sessions/{session_id}/atc?apikey={IF_API_KEY}"
            ) as resp:
                atc_data = await resp.json()

        atc_list = atc_data.get("result", [])

        if not atc_list:
            return await interaction.followup.send("❌ No active ATC")

        # Group by airport
        airports = {}
        for atc in atc_list:
            airport = atc.get("airportIcao")
            if airport:
                airports.setdefault(airport, []).append(atc)

        # Send dropdown
        await interaction.followup.send(
            "✈️ Select an airport with active ATC:",
            view=ATCView(airports, session_id)
        )


async def setup(bot):
    await bot.add_cog(ATC(bot))

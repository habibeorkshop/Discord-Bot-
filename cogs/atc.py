import discord
from discord.ext import commands
from discord import app_commands
import aiohttp
import os

IF_API_KEY = os.getenv("IF_API_KEY")
GUILD_ID = 1493552564799672320
BASE_URL = "https://api.infiniteflight.com/public/v2"

SERVER_MAP = {
    "Casual": "casual",
    "Training": "training",
    "Expert": "expert"
}


# ================= AIRPORT SELECT =================

class AirportSelect(discord.ui.Select):
    def __init__(self, airports, session_id, server_name):
        self.airports = airports
        self.session_id = session_id
        self.server_name = server_name

        options = [
            discord.SelectOption(label=icao)
            for icao in list(airports.keys())[:25]
        ]

        super().__init__(
            placeholder="Select airport...",
            options=options,
            custom_id="atc_airport_select"
        )

    async def callback(self, interaction: discord.Interaction):
        await interaction.response.defer()

        airport = self.values[0]
        atc_units = self.airports.get(airport, [])

        controllers = []
        for atc in atc_units:
            name = atc.get("username", "Unknown")
            freq = atc.get("frequency", "N/A")
            controllers.append(f"{name} ({freq})")

        controller_text = "\n".join(controllers) or "No controllers"

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

        embed = discord.Embed(
            title=f"📡 ATC — {airport}",
            color=discord.Color.green()
        )

        embed.add_field(name="👨‍✈️ Controllers", value=controller_text[:1000], inline=False)
        embed.add_field(name="📊 Traffic", value=f"🛬 {inbound} | 🛫 {outbound}", inline=False)
        embed.add_field(name="🌐 Server", value=self.server_name)

        await interaction.followup.send(embed=embed)


# ================= SERVER SELECT =================

class ServerSelect(discord.ui.Select):
    def __init__(self):
        super().__init__(
            placeholder="Select server...",
            options=[
                discord.SelectOption(label="Casual", emoji="🟢"),
                discord.SelectOption(label="Training", emoji="🟡"),
                discord.SelectOption(label="Expert", emoji="🔴"),
            ],
            custom_id="atc_server_select"
        )

    async def callback(self, interaction: discord.Interaction):
        await interaction.response.defer(ephemeral=True)

        server_choice = self.values[0]
        server_key = SERVER_MAP[server_choice]

        # 🔄 GET SESSION
        async with aiohttp.ClientSession() as session:
            async with session.get(f"{BASE_URL}/sessions?apikey={IF_API_KEY}") as resp:
                sessions = await resp.json()

        session_id = None
        for s in sessions.get("result", []):
            if server_key in s.get("name", "").lower():
                session_id = s.get("id")
                break

        if not session_id:
            return await interaction.followup.send("❌ Server not found")

        # 📡 GET ATC
        async with aiohttp.ClientSession() as session:
            async with session.get(
                f"{BASE_URL}/sessions/{session_id}/atc?apikey={IF_API_KEY}"
            ) as resp:
                atc_data = await resp.json()

        atc_list = atc_data.get("result", [])

        if not atc_list:
            return await interaction.followup.send(
                f"❌ No active ATC on {server_choice}"
            )

        # 🏢 GROUP AIRPORTS
        airports = {}
        for atc in atc_list:
            icao = atc.get("airportIcao")
            if icao:
                airports.setdefault(icao, []).append(atc)

        # 🚨 FIX: CHECK EMPTY
        if not airports:
            return await interaction.followup.send(
                "❌ No airports with ATC found"
            )

        # ✅ CREATE DROPDOWN ONLY IF DATA EXISTS
        view = discord.ui.View(timeout=120)
        view.add_item(AirportSelect(airports, session_id, server_choice))

        await interaction.followup.send(
            f"✈️ Active ATC Airports ({server_choice})",
            view=view,
            ephemeral=True
        )


# ================= VIEW =================

class ATCView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=120)
        self.add_item(ServerSelect())


# ================= COG =================

class ATC(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="atc", description="Active ATC airports")
    @app_commands.guilds(discord.Object(id=GUILD_ID))
    async def atc(self, interaction: discord.Interaction):

        if not IF_API_KEY:
            return await interaction.response.send_message(
                "❌ API key missing",
                ephemeral=True
            )

        await interaction.response.send_message(
            "🛰️ Select server:",
            view=ATCView(),
            ephemeral=True
        )


async def setup(bot):
    await bot.add_cog(ATC(bot))

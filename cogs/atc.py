import discord
from discord.ext import commands
from discord import app_commands
import aiohttp
import os

# 🔧 CONFIG
IF_API_KEY = os.getenv("IF_API_KEY")
GUILD_ID = 1493552564799672320
BASE_URL = "https://api.infiniteflight.com/public/v2"

SERVER_MAP = {
    "Casual": "casual",
    "Training": "training",
    "Expert": "expert"
}


class ATC(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="atc", description="Get ATC info for an airport")
    @app_commands.guilds(discord.Object(id=GUILD_ID))
    @app_commands.describe(
        airport="Airport ICAO (e.g. VABB, EGLL)",
        server="Select server"
    )
    @app_commands.choices(server=[
        app_commands.Choice(name="Casual", value="Casual"),
        app_commands.Choice(name="Training", value="Training"),
        app_commands.Choice(name="Expert", value="Expert"),
    ])
    async def atc(self, interaction: discord.Interaction, airport: str, server: app_commands.Choice[str]):

        await interaction.response.defer()

        airport = airport.upper()
        server_choice = server.value
        server_key = SERVER_MAP[server_choice]

        # ================= GET SESSION =================
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

        # ================= GET ATC =================
        async with aiohttp.ClientSession() as session:
            async with session.get(
                f"{BASE_URL}/sessions/{session_id}/atc?apikey={IF_API_KEY}"
            ) as resp:
                atc_data = await resp.json()

        atc_list = atc_data.get("result", [])

        # Filter for this airport
        airport_atc = [
            atc for atc in atc_list
            if atc.get("airportIcao") == airport
        ]

        if not airport_atc:
            return await interaction.followup.send(
                f"❌ No ATC active at {airport} on {server_choice}"
            )

        # ================= FORMAT CONTROLLERS =================
        atc_types = {
            "Ground": [],
            "Tower": [],
            "ATIS": [],
            "Approach": []
        }

        for atc in airport_atc:
            name = atc.get("username", "Unknown")
            freq = atc.get("frequency", "N/A")
            atc_type = atc.get("type", "Other")

            text = f"{name} ({freq})"

            if atc_type in atc_types:
                atc_types[atc_type].append(text)
            else:
                atc_types.setdefault(atc_type, []).append(text)

        # Build display
        controller_text = ""
        for t, users in atc_types.items():
            if users:
                controller_text += f"**{t}**\n" + "\n".join(users) + "\n\n"

        # ================= TRAFFIC =================
        inbound = 0
        outbound = 0

        async with aiohttp.ClientSession() as session:
            async with session.get(
                f"{BASE_URL}/sessions/{session_id}/flights?apikey={IF_API_KEY}"
            ) as resp:
                flights = await resp.json()

        for f in flights.get("result", []):
            if f.get("arrivalAirportIcao") == airport:
                inbound += 1
            if f.get("departureAirportIcao") == airport:
                outbound += 1

        # ================= EMBED =================
        embed = discord.Embed(
            title=f"📡 ATC — {airport}",
            color=discord.Color.blue()
        )

        embed.add_field(
            name="👨‍✈️ Controllers",
            value=controller_text[:1000],
            inline=False
        )

        embed.add_field(
            name="📊 Traffic",
            value=f"🛬 Inbound: {inbound}\n🛫 Outbound: {outbound}",
            inline=False
        )

        embed.add_field(
            name="🌐 Server",
            value=server_choice,
            inline=True
        )

        await interaction.followup.send(embed=embed)


async def setup(bot):
    await bot.add_cog(ATC(bot))

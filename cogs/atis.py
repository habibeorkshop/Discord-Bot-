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


# ================= DROPDOWN =================

class ServerSelect(discord.ui.Select):
    def __init__(self, airport: str):
        self.airport = airport.upper()

        options = [
            discord.SelectOption(label="Casual", emoji="🟢"),
            discord.SelectOption(label="Training", emoji="🟡"),
            discord.SelectOption(label="Expert", emoji="🔴")
        ]

        super().__init__(
            placeholder="Select server...",
            min_values=1,
            max_values=1,
            options=options,
            custom_id="atis_map_v3"
        )

    async def callback(self, interaction: discord.Interaction):
        await interaction.response.defer(ephemeral=True)

        server_choice = self.values[0]
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

        # ================= GET ATIS =================
        async with aiohttp.ClientSession() as session:
            async with session.get(
                f"{BASE_URL}/sessions/{session_id}/airport/{self.airport}/atis?apikey={IF_API_KEY}"
            ) as resp:
                atis_data = await resp.json()

        atis_text = atis_data.get("result") or "No ATIS available"

        # ================= GET METAR =================
        metar_url = f"https://tgftp.nws.noaa.gov/data/observations/metar/stations/{self.airport}.TXT"

        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(metar_url) as resp:
                    raw = await resp.text()
                    metar = raw.split("\n")[1]
        except:
            metar = "Unavailable"

        # ================= TRAFFIC =================
        inbound = 0
        outbound = 0

        async with aiohttp.ClientSession() as session:
            async with session.get(
                f"{BASE_URL}/sessions/{session_id}/flights?apikey={IF_API_KEY}"
            ) as resp:
                flights = await resp.json()

        for f in flights.get("result", []):
            if f.get("arrivalAirportIcao") == self.airport:
                inbound += 1
            if f.get("departureAirportIcao") == self.airport:
                outbound += 1

        # ================= MAP =================
        # OpenStreetMap static preview
        map_url = f"https://static-maps.yandex.ru/1.x/?lang=en-US&ll=0,0&z=10&l=map"

        # NOTE: IF API does not give coords easily → we skip exact location
        # (can upgrade later with airport DB)

        # ================= EMBED =================
        embed = discord.Embed(
            title=f"✈️ {self.airport} Aviation Info",
            color=discord.Color.blue()
        )

        embed.add_field(
            name="📡 ATIS",
            value=f"```{atis_text[:1000]}```",
            inline=False
        )

        embed.add_field(
            name="🌦️ METAR",
            value=f"```{metar}```",
            inline=False
        )

        embed.add_field(
            name="📊 Traffic",
            value=f"🛬 Inbound: {inbound}\n🛫 Outbound: {outbound}",
            inline=False
        )

        embed.set_image(url=map_url)

        embed.add_field(
            name="🌐 Server",
            value=server_choice,
            inline=True
        )

        await interaction.followup.send(embed=embed)


# ================= VIEW =================

class ATISView(discord.ui.View):
    def __init__(self, airport: str):
        super().__init__(timeout=120)
        self.add_item(ServerSelect(airport))


# ================= COG =================

class ATIS(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="atis", description="Full aviation info")
    @app_commands.guilds(discord.Object(id=GUILD_ID))
    async def atis(self, interaction: discord.Interaction, airport: str):

        if not IF_API_KEY:
            return await interaction.response.send_message(
                "❌ API key missing",
                ephemeral=True
            )

        await interaction.response.send_message(
            f"🛰️ Select server for **{airport.upper()}**",
            view=ATISView(airport),
            ephemeral=True
        )


async def setup(bot):
    await bot.add_cog(ATIS(bot))

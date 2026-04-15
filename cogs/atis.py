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
            custom_id="atis_select_v2"
        )

    async def callback(self, interaction: discord.Interaction):
        server_choice = self.values[0]
        server_key = SERVER_MAP[server_choice]

        await interaction.response.defer(ephemeral=True)

        # ================= GET SESSIONS =================
        async with aiohttp.ClientSession() as session:
            async with session.get(f"{BASE_URL}/sessions?apikey={IF_API_KEY}") as resp:
                sessions_data = await resp.json()

        session_id = None
        user_count = "Unknown"

        for s in sessions_data.get("result", []):
            if server_key in s.get("name", "").lower():
                session_id = s.get("id")
                user_count = s.get("userCount", "Unknown")
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
                    metar_raw = await resp.text()
                    metar_lines = metar_raw.split("\n")
                    metar = metar_lines[1] if len(metar_lines) > 1 else "No METAR found"
        except:
            metar = "METAR unavailable"

        # ================= EMBED =================
        embed = discord.Embed(
            title=f"✈️ ATIS + METAR — {self.airport}",
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
            name="📊 Server",
            value=f"{server_choice}",
            inline=True
        )

        embed.add_field(
            name="👥 Traffic",
            value=f"{user_count} pilots",
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

    @app_commands.command(name="atis", description="Get ATIS + METAR + traffic")
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

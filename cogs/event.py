import discord
from discord.ext import commands
from discord import app_commands
from discord.ui import View, Button, Modal, TextInput
from datetime import datetime, timedelta, timezone
import asyncio
import re

# ================= CONFIG =================

STAFF_ROLE_ID = 1493559145876557955
GUILD_ID = 1493552564799672320

IST = timezone(timedelta(hours=5, minutes=30))


# ================= TIME PARSER =================

def parse_datetime(input_str: str):

    input_str = input_str.strip().lower()
    now = datetime.now(IST)

    # in 2h30m
    match = re.match(r"in (\d+)h(?: ?(\d+)m)?", input_str)

    if match:
        hours = int(match.group(1))
        minutes = int(match.group(2)) if match.group(2) else 0

        return now + timedelta(
            hours=hours,
            minutes=minutes
        )

    # tomorrow 18:30
    match = re.match(r"tomorrow (\d{1,2}):(\d{2})", input_str)

    if match:

        hour = int(match.group(1))
        minute = int(match.group(2))

        return datetime(
            now.year,
            now.month,
            now.day,
            hour,
            minute,
            tzinfo=IST
        ) + timedelta(days=1)

    formats = [
        "%Y-%m-%d %H:%M",
        "%d/%m/%Y %H:%M",
        "%Y-%m-%d %I:%M %p",
        "%d/%m/%Y %I:%M %p"
    ]

    for fmt in formats:
        try:
            dt = datetime.strptime(input_str, fmt)
            return dt.replace(tzinfo=IST)
        except:
            continue

    return None


# ================= EVENT VIEW =================

class EventButtons(View):

    def __init__(
        self,
        attendees,
        embed_msg,
        event_time,
        host
    ):

        super().__init__(timeout=None)

        self.attendees = attendees
        self.embed_msg = embed_msg
        self.event_time = event_time
        self.host = host
        self.locked = False

    async def update_embed(self):

        embed = self.embed_msg.embeds[0]

        timestamp = int(
            self.event_time.astimezone(timezone.utc).timestamp()
        )

        attendees_text = (
            "\n".join([f"• {u.mention}" for u in self.attendees])
            if self.attendees
            else "No attendees yet"
        )

        # UPDATE TIME FIELD
        embed.set_field_at(
            0,
            name="🕒 Event Time",
            value=f"📅 <t:{timestamp}:F>\n⏰ <t:{timestamp}:R>",
            inline=False
        )

        # UPDATE ATTENDEES FIELD
        embed.set_field_at(
            1,
            name=f"👥 Attendees ({len(self.attendees)})",
            value=attendees_text,
            inline=False
        )

        # UPDATE STATUS FIELD
        status = "🔒 Locked" if self.locked else "🟢 Open"

        embed.set_field_at(
            2,
            name="📌 Status",
            value=status,
            inline=False
        )

        await self.embed_msg.edit(
            embed=embed,
            view=self
        )

    # ================= JOIN =================

    @discord.ui.button(
        label="Join",
        emoji="✅",
        style=discord.ButtonStyle.success,
        custom_id="event_join"
    )
    async def join_event(
        self,
        interaction: discord.Interaction,
        button: Button
    ):

        if self.locked:
            return await interaction.response.send_message(
                "❌ Event is locked.",
                ephemeral=True
            )

        if interaction.user not in self.attendees:
            self.attendees.append(interaction.user)

        await self.update_embed()

        await interaction.response.send_message(
            "✅ Joined event.",
            ephemeral=True
        )

    # ================= LEAVE =================

    @discord.ui.button(
        label="Leave",
        emoji="❌",
        style=discord.ButtonStyle.danger,
        custom_id="event_leave"
    )
    async def leave_event(
        self,
        interaction: discord.Interaction,
        button: Button
    ):

        if interaction.user in self.attendees:
            self.attendees.remove(interaction.user)

        await self.update_embed()

        await interaction.response.send_message(
            "❌ Removed from event.",
            ephemeral=True
        )

    # ================= LOCK =================

    @discord.ui.button(
        label="Lock",
        emoji="🔒",
        style=discord.ButtonStyle.secondary,
        custom_id="event_lock"
    )
    async def lock_event(
        self,
        interaction: discord.Interaction,
        button: Button
    ):

        if not any(
            role.id == STAFF_ROLE_ID
            for role in interaction.user.roles
        ):
            return await interaction.response.send_message(
                "❌ Staff only.",
                ephemeral=True
            )

        self.locked = True

        await self.update_embed()

        await interaction.response.send_message(
            "🔒 Event locked.",
            ephemeral=True
        )

    # ================= EDIT =================

    @discord.ui.button(
        label="Edit",
        emoji="✏️",
        style=discord.ButtonStyle.primary,
        custom_id="event_edit"
    )
    async def edit_event(
        self,
        interaction: discord.Interaction,
        button: Button
    ):

        if not any(
            role.id == STAFF_ROLE_ID
            for role in interaction.user.roles
        ):
            return await interaction.response.send_message(
                "❌ Staff only.",
                ephemeral=True
            )

        await interaction.response.send_modal(
            EventEditModal(self)
        )


# ================= EDIT MODAL =================

class EventEditModal(Modal):

    def __init__(self, view):

        super().__init__(title="Edit Event")

        self.view_ref = view

        embed = view.embed_msg.embeds[0]

        self.title_input = TextInput(
            label="Title",
            default=embed.title,
            required=False
        )

        self.desc_input = TextInput(
            label="Description",
            style=discord.TextStyle.paragraph,
            default=embed.description,
            required=False
        )

        self.time_input = TextInput(
            label="Datetime (IST)",
            default=view.event_time.strftime("%Y-%m-%d %H:%M"),
            required=False
        )

        self.add_item(self.title_input)
        self.add_item(self.desc_input)
        self.add_item(self.time_input)

    async def on_submit(self, interaction: discord.Interaction):

        embed = self.view_ref.embed_msg.embeds[0]

        if self.title_input.value:
            embed.title = self.title_input.value

        if self.desc_input.value:
            embed.description = self.desc_input.value

        if self.time_input.value:

            new_dt = parse_datetime(self.time_input.value)

            if not new_dt:
                return await interaction.response.send_message(
                    "❌ Invalid datetime.",
                    ephemeral=True
                )

            self.view_ref.event_time = new_dt

        await self.view_ref.update_embed()

        await interaction.response.send_message(
            "✅ Event updated.",
            ephemeral=True
        )


# ================= COG =================

class Event(commands.Cog):

    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(
        name="createevent",
        description="Create advanced event"
    )
    @app_commands.guilds(
        discord.Object(id=GUILD_ID)
    )
    async def createevent(
        self,
        interaction: discord.Interaction,
        title: str,
        datetime: str,
        description: str,
        channel: discord.TextChannel,
        image: str = None,
        create_ping: discord.Role = None,
        start_ping: discord.Role = None
    ):

        # STAFF ONLY
        if not any(
            role.id == STAFF_ROLE_ID
            for role in interaction.user.roles
        ):
            return await interaction.response.send_message(
                "❌ Staff only.",
                ephemeral=True
            )

        dt = parse_datetime(datetime)

        if not dt:
            return await interaction.response.send_message(
                "❌ Invalid datetime.",
                ephemeral=True
            )

        timestamp = int(
            dt.astimezone(timezone.utc).timestamp()
        )

        embed = discord.Embed(
            title=f"🎉 {title}",
            description=description,
            color=discord.Color.orange()
        )

        embed.add_field(
            name="🕒 Event Time",
            value=f"📅 <t:{timestamp}:F>\n⏰ <t:{timestamp}:R>",
            inline=False
        )

        embed.add_field(
            name="👥 Attendees (0)",
            value="No attendees yet",
            inline=False
        )

        embed.add_field(
            name="📌 Status",
            value="🟢 Open",
            inline=False
        )

        embed.set_footer(
            text=f"Hosted by {interaction.user}",
            icon_url=interaction.user.display_avatar.url
        )

        if image:
            embed.set_image(url=image)

        msg = await channel.send(
            content=create_ping.mention if create_ping else None,
            embed=embed
        )

        attendees = []

        view = EventButtons(
            attendees,
            msg,
            dt,
            interaction.user
        )

        await msg.edit(view=view)

        await interaction.response.send_message(
            f"✅ Event created in {channel.mention}",
            ephemeral=True
        )

        # ================= WAIT FOR EVENT =================

        while datetime.now(timezone.utc) < dt.astimezone(timezone.utc):
            await asyncio.sleep(15)

        # LOCK EVENT
        view.locked = True

        await view.update_embed()

        # START EMBED
        start_embed = discord.Embed(
            title=f"🚀 {title} Started!",
            description="The event is now live!",
            color=discord.Color.green()
        )

        start_embed.add_field(
            name="👥 Participants",
            value=(
                "\n".join([u.mention for u in attendees])
                if attendees
                else "No attendees"
            ),
            inline=False
        )

        # START PING FIXED
        await channel.send(
            content=start_ping.mention if start_ping else None,
            embed=start_embed
        )

        # UPDATE MAIN EMBED STATUS
        final_embed = msg.embeds[0]

        final_embed.set_field_at(
            2,
            name="📌 Status",
            value="🚀 Started",
            inline=False
        )

        await msg.edit(
            embed=final_embed,
            view=view
        )


# ================= SETUP =================

async def setup(bot):
    await bot.add_cog(Event(bot))

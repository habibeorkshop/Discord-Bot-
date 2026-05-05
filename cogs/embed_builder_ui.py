import discord
from discord.ext import commands
from discord import app_commands

# ================= MODAL =================

class EmbedModal(discord.ui.Modal, title="Edit Embed"):

    title_input = discord.ui.TextInput(label="Title", required=False)
    description_input = discord.ui.TextInput(label="Description", style=discord.TextStyle.long)
    color_input = discord.ui.TextInput(label="Hex Color (e.g. #ff9900)", required=False)

    image_input = discord.ui.TextInput(label="Image URL", required=False)
    thumbnail_input = discord.ui.TextInput(label="Thumbnail URL", required=False)
    footer_input = discord.ui.TextInput(label="Footer", required=False)

    def __init__(self, view):
        super().__init__()
        self.view = view

    async def on_submit(self, interaction: discord.Interaction):

        # 🎨 Color handling
        color = discord.Color.orange()
        if self.color_input.value:
            try:
                color = discord.Color(int(self.color_input.value.replace("#", ""), 16))
            except:
                pass

        embed = discord.Embed(
            title=self.title_input.value or None,
            description=self.description_input.value or "No description",
            color=color
        )

        if self.image_input.value:
            embed.set_image(url=self.image_input.value)

        if self.thumbnail_input.value:
            embed.set_thumbnail(url=self.thumbnail_input.value)

        if self.footer_input.value:
            embed.set_footer(text=self.footer_input.value)

        # Add fields
        for field in self.view.fields:
            embed.add_field(name=field["name"], value=field["value"], inline=False)

        self.view.embed = embed

        await interaction.response.defer()
        await self.view.update_preview()


# ================= FIELD MODAL =================

class FieldModal(discord.ui.Modal, title="Add Field"):
    name = discord.ui.TextInput(label="Field Name")
    value = discord.ui.TextInput(label="Field Value", style=discord.TextStyle.long)

    def __init__(self, view):
        super().__init__()
        self.view = view

    async def on_submit(self, interaction: discord.Interaction):
        self.view.fields.append({
            "name": self.name.value,
            "value": self.value.value
        })
        await interaction.response.send_message("✅ Field added!", ephemeral=True)


# ================= BUTTON MODAL =================

class ButtonModal(discord.ui.Modal, title="Add Button"):
    label = discord.ui.TextInput(label="Button Label")
    url = discord.ui.TextInput(label="Button URL")

    def __init__(self, view):
        super().__init__()
        self.view = view

    async def on_submit(self, interaction: discord.Interaction):
        self.view.buttons.append({
            "label": self.label.value,
            "url": self.url.value
        })
        await interaction.response.send_message("✅ Button added!", ephemeral=True)


# ================= MAIN VIEW =================

class EmbedView(discord.ui.View):

    def __init__(self, author):
        super().__init__(timeout=900)
        self.author = author
        self.embed = None
        self.channel = None
        self.fields = []
        self.buttons = []
        self.role_ping = None
        self.message = None

    # 🔁 Update preview
    async def update_preview(self):
        if not self.message:
            return

        try:
            await self.message.edit(
                content="🧪 **Preview**",
                embed=self.embed,
                view=self
            )
        except:
            pass

    # 🔘 Build URL buttons
    def build_buttons(self):
        view = discord.ui.View()
        for b in self.buttons:
            view.add_item(discord.ui.Button(label=b["label"], url=b["url"]))
        return view

    # ================= BUTTONS =================

    @discord.ui.button(label="✏️ Edit", style=discord.ButtonStyle.primary)
    async def edit(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user != self.author:
            return await interaction.response.send_message("❌ Not your panel", ephemeral=True)
        await interaction.response.send_modal(EmbedModal(self))

    @discord.ui.button(label="➕ Field", style=discord.ButtonStyle.secondary)
    async def add_field(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user != self.author:
            return await interaction.response.send_message("❌ Not your panel", ephemeral=True)
        await interaction.response.send_modal(FieldModal(self))

    @discord.ui.button(label="🔘 Button", style=discord.ButtonStyle.secondary)
    async def add_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user != self.author:
            return await interaction.response.send_message("❌ Not your panel", ephemeral=True)
        await interaction.response.send_modal(ButtonModal(self))

    @discord.ui.button(label="👁️ Preview", style=discord.ButtonStyle.secondary)
    async def preview(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self.update_preview()
        await interaction.response.send_message("🔄 Preview updated!", ephemeral=True)

    @discord.ui.button(label="🧹 Reset", style=discord.ButtonStyle.danger)
    async def reset(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user != self.author:
            return await interaction.response.send_message("❌ Not your panel", ephemeral=True)

        self.embed = None
        self.fields.clear()
        self.buttons.clear()

        await interaction.response.send_message("🧹 Builder reset!", ephemeral=True)

        if self.message:
            await self.message.edit(content="Reset. Start again.", embed=None)

    # ================= SELECTS =================

    @discord.ui.select(
        placeholder="📢 Select role to ping",
        cls=discord.ui.RoleSelect,
        min_values=0,
        max_values=1
    )
    async def select_role(self, interaction: discord.Interaction, select):
        if interaction.user != self.author:
            return await interaction.response.send_message("❌ Not yours", ephemeral=True)

        self.role_ping = select.values[0] if select.values else None

        await interaction.response.send_message(
            f"📢 Role set: {self.role_ping.mention if self.role_ping else 'None'}",
            ephemeral=True
        )

    @discord.ui.select(
        placeholder="📍 Select channel",
        cls=discord.ui.ChannelSelect,
        channel_types=[discord.ChannelType.text]
    )
    async def select_channel(self, interaction: discord.Interaction, select):
        if interaction.user != self.author:
            return await interaction.response.send_message("❌ Not yours", ephemeral=True)

        self.channel = select.values[0]

        await interaction.response.send_message(
            f"📍 Channel: {self.channel.mention}",
            ephemeral=True
        )

    # ================= SEND =================

    @discord.ui.button(label="📤 Send", style=discord.ButtonStyle.success)
    async def send(self, interaction: discord.Interaction, button: discord.ui.Button):

        if interaction.user != self.author:
            return await interaction.response.send_message("❌ Not your panel", ephemeral=True)

        if not self.embed:
            return await interaction.response.send_message("❌ Create embed first", ephemeral=True)

        if not self.channel:
            return await interaction.response.send_message("❌ Select channel first", ephemeral=True)

        await interaction.response.defer(ephemeral=True)

        try:
            await self.channel.send(
                content=self.role_ping.mention if self.role_ping else None,
                embed=self.embed,
                view=self.build_buttons() if self.buttons else None
            )

            await interaction.followup.send("✅ Sent successfully!", ephemeral=True)

        except Exception as e:
            await interaction.followup.send(f"❌ Error: {e}", ephemeral=True)


# ================= COMMAND =================

class EmbedBuilder(commands.Cog):

    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="embedui", description="Advanced embed builder")
    async def embedui(self, interaction: discord.Interaction):

        view = EmbedView(interaction.user)

        await interaction.response.send_message(
            "🛠️ **Advanced Embed Builder**\n\n"
            "✏️ Edit\n➕ Field\n🔘 Button\n👁️ Preview\n🧹 Reset\n📤 Send",
            view=view,
            ephemeral=True
        )

        view.message = await interaction.original_response()


async def setup(bot):
    await bot.add_cog(EmbedBuilder(bot))

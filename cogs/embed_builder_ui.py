import discord
from discord.ext import commands
from discord import app_commands

# ================= MODAL =================

class EmbedModal(discord.ui.Modal, title="Edit Embed"):

    title_input = discord.ui.TextInput(
        label="Title",
        required=False
    )

    description_input = discord.ui.TextInput(
        label="Description",
        style=discord.TextStyle.paragraph,
        required=False
    )

    color_input = discord.ui.TextInput(
        label="Hex Color (#ff0000)",
        required=False
    )

    image_input = discord.ui.TextInput(
        label="Image URL",
        required=False
    )

    thumbnail_input = discord.ui.TextInput(
        label="Thumbnail URL",
        required=False
    )

    def __init__(self, view):
        super().__init__()
        self.view_obj = view

    async def on_submit(self, interaction: discord.Interaction):

        # ================= COLOR =================

        color = discord.Color.red()

        if self.color_input.value:
            try:
                color = discord.Color(
                    int(self.color_input.value.replace("#", ""), 16)
                )
            except:
                pass

        # ================= EMBED =================

        embed = discord.Embed(
            title=self.title_input.value or None,
            description=self.description_input.value or "No description provided.",
            color=color
        )

        if self.image_input.value:
            embed.set_image(url=self.image_input.value)

        if self.thumbnail_input.value:
            embed.set_thumbnail(url=self.thumbnail_input.value)

        if self.footer_input.value:
            embed.set_footer(text=self.footer_input.value)

        # ================= FIELDS =================

        for field in self.view_obj.fields:
            embed.add_field(
                name=field["name"],
                value=field["value"],
                inline=False
            )

        self.view_obj.embed = embed

        # ================= UPDATE =================

        await interaction.response.defer(ephemeral=True)

        await self.view_obj.update_preview()

        await interaction.followup.send(
            "✅ Embed updated.",
            ephemeral=True
        )


# ================= FIELD MODAL =================

class FieldModal(discord.ui.Modal, title="Add Field"):

    field_name = discord.ui.TextInput(
        label="Field Name"
    )

    field_value = discord.ui.TextInput(
        label="Field Value",
        style=discord.TextStyle.paragraph
    )

    def __init__(self, view):
        super().__init__()
        self.view_obj = view

    async def on_submit(self, interaction: discord.Interaction):

        self.view_obj.fields.append({
            "name": self.field_name.value,
            "value": self.field_value.value
        })

        # Auto update embed preview
        if self.view_obj.embed:
            self.view_obj.embed.add_field(
                name=self.field_name.value,
                value=self.field_value.value,
                inline=False
            )

        await interaction.response.defer(ephemeral=True)

        await self.view_obj.update_preview()

        await interaction.followup.send(
            "✅ Field added.",
            ephemeral=True
        )


# ================= BUTTON MODAL =================

class ButtonModal(discord.ui.Modal, title="Add Button"):

    label = discord.ui.TextInput(
        label="Button Label"
    )

    url = discord.ui.TextInput(
        label="Button URL"
    )

    def __init__(self, view):
        super().__init__()
        self.view_obj = view

    async def on_submit(self, interaction: discord.Interaction):

        self.view_obj.buttons.append({
            "label": self.label.value,
            "url": self.url.value
        })

        await interaction.response.send_message(
            "✅ Button added.",
            ephemeral=True
        )


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

    # ================= UPDATE PREVIEW =================

    async def update_preview(self):

        if not self.message:
            return

        try:
            await self.message.edit(
                content="🧪 **Embed Preview**",
                embed=self.embed,
                view=self
            )

        except Exception as e:
            print(f"Preview Error: {e}")

    # ================= BUILD BUTTONS =================

    def build_buttons(self):

        view = discord.ui.View()

        for btn in self.buttons:
            view.add_item(
                discord.ui.Button(
                    label=btn["label"],
                    url=btn["url"]
                )
            )

        return view

    # ================= EDIT =================

    @discord.ui.button(
        label="✏️ Edit",
        style=discord.ButtonStyle.primary
    )
    async def edit_embed(
        self,
        interaction: discord.Interaction,
        button: discord.ui.Button
    ):

        if interaction.user != self.author:
            return await interaction.response.send_message(
                "❌ Not your panel.",
                ephemeral=True
            )

        await interaction.response.send_modal(
            EmbedModal(self)
        )

    # ================= ADD FIELD =================

    @discord.ui.button(
        label="➕ Field",
        style=discord.ButtonStyle.secondary
    )
    async def add_field_button(
        self,
        interaction: discord.Interaction,
        button: discord.ui.Button
    ):

        if interaction.user != self.author:
            return await interaction.response.send_message(
                "❌ Not your panel.",
                ephemeral=True
            )

        await interaction.response.send_modal(
            FieldModal(self)
        )

    # ================= ADD BUTTON =================

    @discord.ui.button(
        label="🔘 Button",
        style=discord.ButtonStyle.secondary
    )
    async def add_button_button(
        self,
        interaction: discord.Interaction,
        button: discord.ui.Button
    ):

        if interaction.user != self.author:
            return await interaction.response.send_message(
                "❌ Not your panel.",
                ephemeral=True
            )

        await interaction.response.send_modal(
            ButtonModal(self)
        )

    # ================= PREVIEW =================

    @discord.ui.button(
        label="👁️ Preview",
        style=discord.ButtonStyle.secondary
    )
    async def preview_embed(
        self,
        interaction: discord.Interaction,
        button: discord.ui.Button
    ):

        await self.update_preview()

        await interaction.response.send_message(
            "🔄 Preview updated.",
            ephemeral=True
        )

    # ================= RESET =================

    @discord.ui.button(
        label="🧹 Reset",
        style=discord.ButtonStyle.danger
    )
    async def reset_embed(
        self,
        interaction: discord.Interaction,
        button: discord.ui.Button
    ):

        if interaction.user != self.author:
            return await interaction.response.send_message(
                "❌ Not your panel.",
                ephemeral=True
            )

        self.embed = None
        self.fields.clear()
        self.buttons.clear()

        await interaction.response.send_message(
            "🧹 Builder reset.",
            ephemeral=True
        )

        try:
            await self.message.edit(
                content="🧹 Builder reset.",
                embed=None,
                view=self
            )
        except:
            pass

    # ================= ROLE SELECT =================

    @discord.ui.select(
        placeholder="📢 Select role to ping",
        cls=discord.ui.RoleSelect,
        min_values=0,
        max_values=1
    )
    async def select_role(self, interaction, select):

        self.role_ping = select.values[0] if select.values else None

        await interaction.response.send_message(
            f"📢 Role selected: {self.role_ping.mention if self.role_ping else 'None'}",
            ephemeral=True
        )

    # ================= CHANNEL SELECT =================

    @discord.ui.select(
        placeholder="📍 Select channel",
        cls=discord.ui.ChannelSelect,
        channel_types=[discord.ChannelType.text]
    )
    async def select_channel(self, interaction, select):

        self.channel = select.values[0]

        await interaction.response.send_message(
            f"📍 Channel selected: {self.channel.mention}",
            ephemeral=True
        )

    # ================= SEND =================

    @discord.ui.button(
        label="📤 Send",
        style=discord.ButtonStyle.success
    )
    async def send_embed(
        self,
        interaction: discord.Interaction,
        button: discord.ui.Button
    ):

        if interaction.user != self.author:
            return await interaction.response.send_message(
                "❌ Not your panel.",
                ephemeral=True
            )

        if not self.embed:
            return await interaction.response.send_message(
                "❌ Create embed first.",
                ephemeral=True
            )

        if not self.channel:
            return await interaction.response.send_message(
                "❌ Select a channel first.",
                ephemeral=True
            )

        await interaction.response.defer(ephemeral=True)

        try:

            await self.channel.send(
                content=self.role_ping.mention if self.role_ping else None,
                embed=self.embed,
                view=self.build_buttons() if self.buttons else None
            )

            await interaction.followup.send(
                "✅ Embed sent successfully.",
                ephemeral=True
            )

        except Exception as e:

            await interaction.followup.send(
                f"❌ Error: {e}",
                ephemeral=True
            )


# ================= COG =================

class EmbedBuilder(commands.Cog):

    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(
        name="embedui",
        description="Advanced Embed Builder"
    )
    async def embedui(self, interaction: discord.Interaction):

        view = EmbedView(interaction.user)

        await interaction.response.send_message(
            "🛠️ **Advanced Embed Builder**\n\n"
            "✏️ Edit Embed\n"
            "➕ Add Fields\n"
            "🔘 Add URL Buttons\n"
            "👁️ Preview Embed\n"
            "🧹 Reset Builder\n"
            "📤 Send Embed",
            view=view,
            ephemeral=True
        )

        view.message = await interaction.original_response()


# ================= SETUP =================

async def setup(bot):
    await bot.add_cog(EmbedBuilder(bot))

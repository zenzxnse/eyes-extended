import discord
from discord.ext import commands
from discord import app_commands
import aiosqlite, aiohttp
import asyncio, json
import motor.motor_asyncio
import traceback, re
from colorama import Fore, Style
from urllib.parse import urlparse
from Extensions.Utility.roles import RoleMenuView  # Import the RoleMenuView class
from typing import Optional
from discord import app_commands, Webhook, TextChannel, HTTPException, Interaction
import datetime

# import logging

# logging.basicConfig(level=logging.DEBUG)

def is_valid_url(url):
    try:
        result = urlparse(url)
        return all([result.scheme, result.netloc])
    except ValueError:
        return False

class EmbedbuilderButtons(discord.ui.View):
    def __init__(self, bot, user_id, embed_name):
        super().__init__(timeout=600)
        self.bot = bot
        self.user_id = user_id
        self.embed_name = embed_name

    @discord.ui.button(label="Edit Embed", style=discord.ButtonStyle.blurple, emoji="<a:pencil_cc:1235842878740238347>")
    async def edit_embed(self, interaction: discord.Interaction, button: discord.ui.Button):
        # Fetch the current embed data
        embed_project_cog = self.bot.get_cog("EmbedProject")
        if not embed_project_cog:
            await interaction.response.send_message("Embed management functionality is currently unavailable.", ephemeral=True)
            return

        embed_data = await embed_project_cog.retrieve_embed_data(self.user_id, self.embed_name)
        if not embed_data:
            await interaction.response.send_message("Failed to retrieve embed data.", ephemeral=True)
            return

        # Assuming `retrieve_embed_data` returns an instance of `discord.Embed`
        await interaction.response.send_message("Edit your embed:", embed=embed_data, view=EmbedEditButtons(self.bot, self.user_id, self.embed_name), ephemeral=True)

    @discord.ui.button(label="Add Button", style=discord.ButtonStyle.grey, emoji="<:plus:1235848647531298876>")
    async def add_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_message("Choose a button style:", view=ButtonLookView(self.bot, self.embed_name), ephemeral=True)

    @discord.ui.button(label="Remove Button", style=discord.ButtonStyle.gray, emoji="<:delete:1233761545754771546>")
    async def remove_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_modal(RemoveButtonModal(self.bot, self.user_id, self.embed_name))

    @discord.ui.button(label="Reveal Embed", style=discord.ButtonStyle.gray, row=2, emoji="<a:fire:1235847103041900554>")
    async def reveal_embed(self, interaction: discord.Interaction, button: discord.ui.Button):
        embed_project_cog = self.bot.get_cog("EmbedProject")
        if not embed_project_cog:
            await interaction.response.send_message("Embed management functionality is currently unavailable.", ephemeral=True)
            return
        embed_data = await embed_project_cog.retrieve_embed_data(self.user_id, self.embed_name, include_view=True)
        if embed_data:
            embed, view = embed_data  # Unpack both embed and view
            await interaction.response.send_message(embed=embed, view=view, ephemeral=True)  # Use the view that is either dynamically created or a default empty view
        else:
            await interaction.response.send_message("No embed found with that name.", ephemeral=True)
    @discord.ui.button(label="Delete Embed", style=discord.ButtonStyle.gray, row=2, emoji="<:del:1235849127179452468>")
    async def remove_embed(self, interaction: discord.Interaction, button: discord.ui.Button):
        delete_confirm_embed = discord.Embed(
            title="<:del:1235849127179452468> Delete Embed",
            description="Are you sure you want to delete this embed?",
            color=0x2F3136
        )
        delete_confirm_embed.set_footer(text=f"Requested by {interaction.user}", icon_url=interaction.user.avatar.url)
        delete_confirm_embed.timestamp = discord.utils.utcnow()
        await interaction.response.send_message(embed=delete_confirm_embed, view=DeleteEmbedView(self.bot, self.user_id, self.embed_name), ephemeral=True)
    

        
class DeleteEmbedView(discord.ui.View):
    def __init__(self, bot, user_id, embed_name):
        super().__init__()
        self.bot = bot
        self.user_id = user_id
        self.embed_name = embed_name
    
    @discord.ui.button(label="Yes", style=discord.ButtonStyle.red)
    async def remove_embed(self, interaction: discord.Interaction, button: discord.ui.Button):
        embed_project_cog = self.bot.get_cog("EmbedProject")
        if not embed_project_cog:
            await interaction.response.send_message("Embed management functionality is currently unavailable.", ephemeral=True)
            return

        # Delete the embed
        await embed_project_cog.delete_embed(self.user_id, self.embed_name)

        # Delete associated buttons
        success, message = await embed_project_cog.delete_buttons_for_embed_db(self.user_id, self.embed_name)
        if not success:
            await interaction.response.send_message(f"Failed to delete buttons for '{self.embed_name}': {message}", ephemeral=True)
            return

        await interaction.response.send_message(f"Embed '{self.embed_name}' and its buttons have been successfully deleted.", ephemeral=True)

    

class RemoveButtonModal(discord.ui.Modal, title="Remove a Button"):
    def __init__(self, bot, user_id, embed_name):
        super().__init__()
        self.bot = bot
        self.user_id = user_id
        self.embed_name = embed_name
        self.add_item(discord.ui.TextInput(
            label="Button Custom ID",
            placeholder="Enter the custom ID of the button to remove...",
            custom_id="custom_id_input",
            style=discord.TextStyle.short,
            required=True
        ))

    async def on_submit(self, interaction: discord.Interaction):
        custom_id = self.children[0].value
        embed_project_cog = self.bot.get_cog("EmbedProject")
        if not embed_project_cog:
            await interaction.response.send_message("Embed management functionality is currently unavailable.", ephemeral=True)
            return

        success, message = await embed_project_cog.delete_button_info_db(self.user_id, custom_id)
        if success:
            await interaction.response.send_message("Button removed successfully.", ephemeral=True)
        else:
            await interaction.response.send_message(message, ephemeral=True)
class EmbedEditButtons(discord.ui.View):
    def __init__(self, bot, user_id, embed_name):
        super().__init__(timeout=600)
        self.bot = bot
        self.user_id = user_id
        self.embed_name = embed_name
    
    async def update_embed_message(self, interaction):
        embed = await self.bot.get_cog("EmbedProject").retrieve_embed_data(self.user_id, self.embed_name)
        if embed:
            await interaction.edit_original_response(embed=embed, view=self, ephemeral=True)

    @discord.ui.button(label="Edit Title", style=discord.ButtonStyle.gray)
    async def edit_title(self, interaction: discord.Interaction, button: discord.ui.Button):
        modal = TitleModal(self.bot, self.user_id, self.embed_name, self.update_embed_message)
        await modal.setup()
        await interaction.response.send_modal(modal)

    @discord.ui.button(label="Edit Description", style=discord.ButtonStyle.gray)
    async def edit_description(self, interaction: discord.Interaction, button: discord.ui.Button):
        modal = DescriptionModal(self.bot, self.user_id, self.embed_name, self.update_embed_message)
        await modal.setup()
        await interaction.response.send_modal(modal)
    @discord.ui.button(label="Edit Color", style=discord.ButtonStyle.gray)
    async def edit_color(self, interaction: discord.Interaction, button: discord.ui.Button):
        modal = ColorModal(self.bot, self.user_id, self.embed_name, self.update_embed_message)
        await modal.setup()
        await interaction.response.send_modal(modal)

    @discord.ui.button(label="Edit Image", style=discord.ButtonStyle.gray)
    async def edit_image(self, interaction: discord.Interaction, button: discord.ui.Button):
        modal = ImageModal(self.bot, self.user_id, self.embed_name, self.update_embed_message)
        await modal.setup()
        await interaction.response.send_modal(modal)
    @discord.ui.button(label="Edit Thumbnail", style=discord.ButtonStyle.gray)
    async def edit_thumbnail(self, interaction: discord.Interaction, button: discord.ui.Button):
        modal = ThumbnailModal(self.bot, self.user_id, self.embed_name, self.update_embed_message)
        await modal.setup()
        await interaction.response.send_modal(modal)
    @discord.ui.button(label="Edit Footer", style=discord.ButtonStyle.gray)
    async def edit_footer(self, interaction: discord.Interaction, button: discord.ui.Button):
        modal = FooterModal(self.bot, self.user_id, self.embed_name, self.update_embed_message)
        await modal.setup()
        await interaction.response.send_modal(modal)
    @discord.ui.button(label="Edit Author", style=discord.ButtonStyle.gray)
    async def edit_author(self, interaction: discord.Interaction, button: discord.ui.Button):
        modal = AuthorModal(self.bot, self.user_id, self.embed_name, self.update_embed_message)
        await modal.setup()
        await interaction.response.send_modal(modal)
    @discord.ui.button(label="Add field", style=discord.ButtonStyle.gray)
    async def add_field(self, interaction: discord.Interaction, button: discord.ui.Button):
        modal = AddFieldModal(self.bot, self.user_id, self.embed_name, self.update_embed_message)
        await interaction.response.send_modal(modal)
    @discord.ui.button(label="Remove field", style=discord.ButtonStyle.gray)
    async def remove_field(self, interaction: discord.Interaction, button: discord.ui.Button):
        modal = RemoveFieldModal(self.bot, self.user_id, self.embed_name, self.update_embed_message)
        await interaction.response.send_modal(modal)

    @discord.ui.button(label="Edit Field", style=discord.ButtonStyle.gray)
    async def edit_field(self, interaction: discord.Interaction, button: discord.ui.Button):
        modal = EditFieldModal(self.bot, self.user_id, self.embed_name, self.update_embed_message)
        await interaction.response.send_modal(modal)

class ButtonLookView(discord.ui.View):
    def __init__(self, bot, embed_name):
        super().__init__()
        self.bot = bot
        self.embed_name = embed_name
        for style in ["Primary", "Secondary", "Success", "Danger"]:
            self.add_item(discord.ui.Button(label=style, style=getattr(discord.ButtonStyle, style.lower()), custom_id=style.lower()))

    async def interaction_check(self, interaction: discord.Interaction):
        selected_style = interaction.data['custom_id']
        await interaction.response.send_modal(ButtonModal(self.bot, selected_style, self.embed_name))

class ButtonModal(discord.ui.Modal, title="Button Details"):
    def __init__(self, bot, style, embed_name):
        super().__init__()
        self.bot = bot
        self.style = style
        self.embed_name = embed_name
        self.add_item(discord.ui.TextInput(label="Button Label", placeholder="Enter the button label or name...", style=discord.TextStyle.short, required=True))
        self.add_item(discord.ui.TextInput(label="Button Emoji", placeholder="Example: <:planet:1223294341204938872> or leave blank...", style=discord.TextStyle.short, required=False))

    async def on_submit(self, interaction: discord.Interaction):
        label = self.children[0].value
        emoji = self.children[1].value or None

        if len(label) > 32:
            embed = discord.Embed(title="<:1001timeout:1233770920099844227> Invalid Input", description="Button label must be 32 characters or fewer.", color=0xFF0000)
            embed.set_footer(text=f"Requested by {interaction.user}", icon_url=interaction.user.avatar.url)
            embed.timestamp = discord.utils.utcnow()
            await interaction.response.send_message(embed=embed, ephemeral=True)
            return

        if emoji and not self.is_valid_emoji(emoji):
            embed = discord.Embed(title="<:1001timeout:1233770920099844227> Invalid Emoji", description="The provided emoji is invalid. Please enter a valid emoji or leave it blank.", color=0xFF0000)
            embed.set_footer(text=f"Requested by {interaction.user}", icon_url=interaction.user.avatar.url)
            embed.timestamp = discord.utils.utcnow()
            await interaction.response.send_message(embed=embed, ephemeral=True)
            return

        embed = discord.Embed(title="<a:83888settingsanimation:1233771395415015524> Button Action", description="What should this button do?", color=0x2F3136)
        embed.set_footer(text=f"Requested by {interaction.user}", icon_url=interaction.user.avatar.url)
        embed.timestamp = discord.utils.utcnow()
        await interaction.response.send_message(embed=embed, view=ButtonDropdownView(self.bot, label, emoji, self.style, self.embed_name), ephemeral=True)

    def is_valid_emoji(self, emoji):
        return emoji.startswith('<:') and emoji.endswith('>') and ':' in emoji

class ButtonDropdownView(discord.ui.View):
    def __init__(self, bot, label, emoji, style, embed_name):
        super().__init__()
        self.bot = bot
        self.label = label
        self.emoji = emoji
        self.style = style
        self.embed_name = embed_name
        self.add_item(ButtonDropdown(bot, label, emoji, style, embed_name))

class ButtonDropdown(discord.ui.Select):
    def __init__(self, bot, label, emoji, style, embed_name):
        super().__init__(placeholder="Select an action", min_values=1, max_values=1)
        self.bot = bot
        self.label = label
        self.emoji = emoji
        self.style = style
        self.embed_name = embed_name
        self.options = [
            discord.SelectOption(label="Give Role", description="Assign a role", emoji="🎭"),
            discord.SelectOption(label="Send An Embedded Message", description="Send an embedded message", emoji="📨"),
            discord.SelectOption(label="Send A Default Message", description="Send a plain message", emoji="💬"),
            discord.SelectOption(label="Sends a role menu", description="Self-role menu configuration", emoji="📋")
        ]

    async def callback(self, interaction: discord.Interaction):
        selected_option = self.values[0]
        if selected_option == "Give Role":
            embed = discord.Embed(title="<:9177neonredarrowright:1240180166089769000> Role Selection", description="Select a role to assign:", color=0x2F3136)
            embed.set_footer(text=f"Requested by {interaction.user}", icon_url=interaction.user.avatar.url)
            embed.timestamp = discord.utils.utcnow()
            await interaction.response.send_message(embed=embed, view=RoleDropdownView(self.bot, interaction.guild.roles, self.label, self.emoji, self.style, self.embed_name), ephemeral=True)
        elif selected_option == "Send An Embedded Message":
            await interaction.response.send_modal(EmbedToButtons(self.bot, interaction.user.id, self.embed_name, self.label, self.emoji, self.style))
        elif selected_option == "Send A Default Message":
            await interaction.response.send_modal(CustomMessageModal(self.bot, self.label, self.emoji, self.style, self.embed_name))
        elif selected_option == "Sends a role menu":
            await interaction.response.send_modal(RoleMenuNameModal(self.bot, interaction.user.id, self.embed_name, self.label, self.emoji, self.style))

class RoleMenuNameModal(discord.ui.Modal, title="Role Menu Name"):
    def __init__(self, bot, user_id, embed_name, label, emoji, style):
        super().__init__()
        self.bot = bot
        self.user_id = user_id
        self.embed_name = embed_name
        self.label = label
        self.emoji = emoji
        self.style = style

        self.role_menu_name = discord.ui.TextInput(
            label="Enter the Role Menu Name",
            placeholder="Type the name of the role menu here...",
            required=True,
            max_length=100
        )
        self.add_item(self.role_menu_name)

    async def on_submit(self, interaction: discord.Interaction):
        role_menu_name = self.role_menu_name.value.strip()
        guild_id = interaction.guild.id
        role_menu_exists = await self.bot.get_cog("Roles").check_role_menu_exists(guild_id, role_menu_name)
        if role_menu_exists:
            additional_data = {'role_menu_name': role_menu_name, 'guild_id': guild_id}
            embed = discord.Embed(title="<a:fire:1235847103041900554> Role Menu Found", description="Role menu found! Finalizing button creation.", color=0x2F3136)
            embed.set_footer(text=f"Requested by {interaction.user}", icon_url=interaction.user.avatar.url)
            embed.timestamp = discord.utils.utcnow()
            await interaction.response.send_message(embed=embed, ephemeral=True)
            await interaction.followup.send(embed=discord.Embed(title="<a:discord_typing:1233761017801211955> Finalizing", description="Finalizing button creation.", color=0x2F3136), view=FinalizeButtonView(self.bot, self.user_id, self.embed_name, self.label, self.emoji, self.style, "Sends a role menu", additional_data), ephemeral=True)
        else:
            embed = discord.Embed(title="<:1001timeout:1233770920099844227> Role Menu Not Found", description="Role menu not found. Please try again.", color=0xFF0000)
            embed.set_footer(text=f"Requested by {interaction.user}", icon_url=interaction.user.avatar.url)
            embed.timestamp = discord.utils.utcnow()
            await interaction.response.send_message(embed=embed, ephemeral=True)

class CustomMessageModal(discord.ui.Modal, title="Custom Message"):
    def __init__(self, bot, label, emoji, style, embed_name):
        super().__init__()
        self.bot = bot
        self.label = label
        self.emoji = emoji
        self.style = style
        self.embed_name = embed_name
        self.add_item(discord.ui.TextInput(
            label="Message Content",
            placeholder="Type your message here...",
            style=discord.TextStyle.paragraph,
            required=True
        ))

    async def on_submit(self, interaction: discord.Interaction):
        custom_message = self.children[0].value
        additional_data = {'custom_message': custom_message}
        embed = discord.Embed(title="<a:discord_typing:1233761017801211955> Finalizing", description="Finalizing button creation.", color=0x2F3136)
        embed.set_footer(text=f"Requested by {interaction.user}", icon_url=interaction.user.avatar.url)
        embed.timestamp = discord.utils.utcnow()
        await interaction.response.send_message(embed=embed, ephemeral=True)
        await interaction.followup.send(view=FinalizeButtonView(self.bot, interaction.user.id, self.embed_name, self.label, self.emoji, self.style, "Send A Default Message", additional_data), ephemeral=True)

class ButtomEmbedMessageView(discord.ui.View):
    def __init__(self, bot, user_id, embed_name):
        super().__init__()
        self.bot = bot
        self.user_id = user_id
        self.embed_name = embed_name

    @discord.ui.button(label="Embed Name", style=discord.ButtonStyle.gray, emoji="<:8355moon:1233771385839681566>")
    async def embed_name(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_modal(EmbedToButtons(self.bot, self.user_id, self.embed_name))

class EmbedToButtons(discord.ui.Modal, title="Embed Name"):
    def __init__(self, bot, user_id, original_embed_name, label, emoji, style):
        super().__init__()
        self.bot = bot
        self.user_id = user_id
        self.original_embed_name = original_embed_name
        self.label = label
        self.emoji = emoji
        self.style = style
        self.send_embed_input = discord.ui.TextInput(
            label="Name Of Embed to Send",
            style=discord.TextStyle.short,
            placeholder="Enter the name of the embed to send...",
            required=True,
            default=original_embed_name
        )
        self.add_item(self.send_embed_input)

    async def on_submit(self, interaction: discord.Interaction):
        send_embed_name = self.send_embed_input.value.strip()
        additional_data = {'send_embed': send_embed_name}
        embed = discord.Embed(title="<a:fire:1235847103041900554> Embed Updated", description=f"Embed to send updated to: **{send_embed_name}**", color=0x2F3136)
        embed.set_footer(text=f"Requested by {interaction.user}", icon_url=interaction.user.avatar.url)
        embed.timestamp = discord.utils.utcnow()
        await interaction.response.send_message(embed=embed, ephemeral=True)
        await interaction.followup.send(embed=discord.Embed(title="<a:discord_typing:1233761017801211955> Finalizing", description="Finalizing button creation.", color=0x2F3136), view=FinalizeButtonView(self.bot, self.user_id, self.original_embed_name, self.label, self.emoji, self.style, "Send An Embedded Message", additional_data), ephemeral=True)

class RoleDropdownView(discord.ui.View):
    def __init__(self, bot, roles, label, emoji, style, embed_name):
        super().__init__()
        self.bot = bot
        self.label = label
        self.emoji = emoji
        self.style = style
        self.embed_name = embed_name  # Store the embed_name
        self.add_item(RoleDropdown(bot, roles, label, emoji, style, embed_name))

class RoleDropdown(discord.ui.Select):
    def __init__(self, bot, roles, label, emoji, style, embed_name):
        super().__init__(placeholder="Choose a role...", min_values=1, max_values=1)
        self.bot = bot
        self.label = label
        self.emoji = emoji
        self.style = style
        self.embed_name = embed_name

        bot_member = bot.get_guild(roles[0].guild.id).me
        bot_highest_role_position = bot_member.top_role.position

        manageable_roles = [
            role for role in roles
            if role.position < bot_highest_role_position and role.name != "@everyone"
        ]

        self.options = [
            discord.SelectOption(label=role.name, description=f"ID: {role.id}", value=str(role.id))
            for role in manageable_roles
        ]

    async def callback(self, interaction: discord.Interaction):
        role_id = self.values[0]
        role = interaction.guild.get_role(int(role_id))
        if role:
            additional_data = {'role_to_give': role_id}
            
            role_selected_embed = discord.Embed(
                title="<:73914home:1233771403845566504> Role Selected",
                description=f"You selected: **{role.name}**",
                color=0x2F3136
            )
            role_selected_embed.set_footer(text=f"Requested by {interaction.user}", icon_url=interaction.user.avatar.url)
            role_selected_embed.timestamp = discord.utils.utcnow()
            await interaction.response.send_message(embed=role_selected_embed, ephemeral=True)

            finalizing_embed = discord.Embed(
                title="<a:discord_typing:1233761017801211955> Finalizing Button",
                description="Finalizing button creation. Please confirm in the next step.",
                color=0x2F3136
            )
            finalizing_embed.set_footer(text=f"Requested by {interaction.user}", icon_url=interaction.user.avatar.url)
            finalizing_embed.timestamp = discord.utils.utcnow()
            await interaction.followup.send(
                embed=finalizing_embed,
                view=FinalizeButtonView(self.bot, interaction.user.id, self.embed_name, self.label, self.emoji, self.style, "Give Role", additional_data),
                ephemeral=True
            )
        else:
            error_embed = discord.Embed(
                title="<:1001timeout:1233770920099844227> Error",
                description="Role not found. Please try again.",
                color=0xFF0000
            )
            error_embed.set_footer(text=f"Requested by {interaction.user}", icon_url=interaction.user.avatar.url)
            error_embed.timestamp = discord.utils.utcnow()
            await interaction.response.send_message(embed=error_embed, ephemeral=True)

class FinalizeButtonView(discord.ui.View):
    def __init__(self, bot, user_id, embed_name, label, emoji, style, functionality, additional_data):
        super().__init__()
        self.bot = bot
        self.user_id = user_id
        self.embed_name = embed_name
        self.label = label
        self.emoji = emoji
        self.style = style
        self.functionality = functionality
        self.additional_data = additional_data

    @discord.ui.button(label="Confirm Button Creation", style=discord.ButtonStyle.green, emoji="<a:fire:1235847103041900554>")
    async def confirm_button_creation(self, interaction: discord.Interaction, button: discord.ui.Button):
        embed_project = self.bot.get_cog("EmbedProject")
        if embed_project:
            style_name = self.style.name if isinstance(self.style, discord.ButtonStyle) else self.style
            custom_id = await embed_project.add_button_info_db(
                self.user_id, self.embed_name, self.label, style_name, None,
                self.emoji, self.additional_data.get('role_to_give'), self.additional_data.get('send_embed'), self.additional_data.get('custom_message'),
                guild_id=self.additional_data.get('guild_id'), role_menu_name=self.additional_data.get('role_menu_name')
            )
            
            success_embed = discord.Embed(
                title="<a:fire:1235847103041900554> Button Created",
                description=f"Button created successfully!\n\n<:9177neonredarrowright:1240180166089769000> **Button ID:** `{custom_id}`\n<:9177neonredarrowright:1240180166089769000> **Embed:** `{self.embed_name}`",
                color=0x2F3136
            )
            success_embed.set_footer(text=f"Requested by {interaction.user}", icon_url=interaction.user.avatar.url)
            success_embed.timestamp = discord.utils.utcnow()
            await interaction.response.send_message(embed=success_embed, ephemeral=True)
        else:
            error_embed = discord.Embed(
                title="<:1001timeout:1233770920099844227> Error",
                description="Failed to access EmbedProject cog. Button not created.",
                color=0xFF0000
            )
            error_embed.set_footer(text=f"Requested by {interaction.user}", icon_url=interaction.user.avatar.url)
            error_embed.timestamp = discord.utils.utcnow()
            await interaction.response.send_message(embed=error_embed, ephemeral=True)
           

# This view is shown after all necessary data is collected
class EditFieldModal(discord.ui.Modal, title='Edit Field'):
    def __init__(self, bot, user_id, embed_name, update_callback):
        super().__init__()
        self.bot = bot
        self.user_id = user_id
        self.embed_name = embed_name
        self.update_callback = update_callback

        # Field ID input (required)
        self.field_id = discord.ui.TextInput(
            label='Field ID',
            style=discord.TextStyle.short,
            placeholder='Enter the ID of the field to edit...',
            required=True
        )
        self.add_item(self.field_id)

        # Field title input (required)
        self.field_title = discord.ui.TextInput(
            label='Field Title',
            style=discord.TextStyle.short,
            placeholder='Enter new field title here...',
            required=True
        )
        self.add_item(self.field_title)

        # Field text input (optional)
        self.field_text = discord.ui.TextInput(
            label='Field Text',
            style=discord.TextStyle.paragraph,
            placeholder='Enter new field text here... (Type None to remove)',
            required=False
        )
        self.add_item(self.field_text)

    async def on_submit(self, interaction: discord.Interaction):
        try:
            field_id = int(self.field_id.value.strip())
        except ValueError:
            await interaction.response.send_message("Invalid input: Field ID must be an integer.", ephemeral=True)
            return

        field_title = self.field_title.value.strip()
        field_text = self.field_text.value.strip() if self.field_text.value else None

        if field_text == 'None':  # Check if the input is explicitly 'None'
            field_text = None  # Set to None to indicate removal of the field text

        try:
            # Attempt to update the field in the embed
            update_success = await self.bot.get_cog("EmbedProject").update_field_in_embed(
                self.user_id, self.embed_name, field_id, field_title, field_text
            )
            if not update_success:
                await interaction.response.send_message("No field found with the specified ID or failed to update the field.", ephemeral=True)
                return

            embed = await self.bot.get_cog("EmbedProject").retrieve_embed_data(self.user_id, self.embed_name)
            if embed:
                await interaction.response.send_message(embed=embed, view=EmbedEditButtons(self.bot, self.user_id, self.embed_name), ephemeral=True)
            else:
                await interaction.response.send_message("Failed to retrieve updated embed data.", ephemeral=True)
        except Exception as e:
            await interaction.response.send_message('Oops! Something went wrong.', ephemeral=True)
            traceback.print_exception(type(e), e, e.__traceback__)

class RemoveFieldModal(discord.ui.Modal, title='Remove Field'):
    def __init__(self, bot, user_id, embed_name, update_callback):
        super().__init__()
        self.bot = bot
        self.user_id = user_id
        self.embed_name = embed_name
        self.update_callback = update_callback

        self.field_position = discord.ui.TextInput(
            label='Field Position',
            style=discord.TextStyle.short,
            placeholder='Enter the position of the field to remove...',
            required=True
        )
        self.add_item(self.field_position)

    async def on_submit(self, interaction: discord.Interaction):
        try:
            position = int(self.field_position.value.strip())
        except ValueError:
            await interaction.response.send_message("Invalid input: Field position must be an integer.", ephemeral=True)
            return

        # Retrieve current fields to check if the position is valid
        embed_fields = await self.bot.get_cog("EmbedProject").get_embed_fields(self.user_id, self.embed_name)
        if not embed_fields:
            await interaction.response.send_message("No fields available to remove. Please add a field first.", ephemeral=True)
            return

        if position < 1 or position > len(embed_fields):
            await interaction.response.send_message(f"Invalid position: Please enter a valid field position between 1 and {len(embed_fields)}.", ephemeral=True)
            return

        try:
            # Remove the field based on its position
            await self.bot.get_cog("EmbedProject").remove_field_from_embed(self.user_id, self.embed_name, position)
            embed = await self.bot.get_cog("EmbedProject").retrieve_embed_data(self.user_id, self.embed_name)
            if embed:
                await interaction.response.send_message(embed=embed, view=EmbedEditButtons(self.bot, self.user_id, self.embed_name), ephemeral=True)
            else:
                await interaction.response.send_message("Failed to remove the field.", ephemeral=True)
        except Exception as e:
            await interaction.response.send_message('Oops! Something went wrong.', ephemeral=True)
            traceback.print_exception(type(e), e, e.__traceback__)
class AddFieldModal(discord.ui.Modal, title='Add Field'):
    def __init__(self, bot, user_id, embed_name, update_callback):
        super().__init__()
        self.bot = bot
        self.user_id = user_id
        self.embed_name = embed_name
        self.update_callback = update_callback

        # Field title input (required)
        self.field_title = discord.ui.TextInput(
            label='Field Title',
            style=discord.TextStyle.short,
            placeholder='Enter field title here...',
            required=True  # This field is required
        )
        self.add_item(self.field_title)

        # Field description input (optional)
        self.field_description = discord.ui.TextInput(
            label='Field Description',
            style=discord.TextStyle.paragraph,
            placeholder='Enter field description here... (optional)',
            required=False  # This field is optional
        )
        self.field_inline = discord.ui.TextInput(
            label='Should be inline or not?',
            style=discord.TextStyle.short,
            placeholder='True (optional by default this is False)',
            required=False  # This field is optional
        )
        self.add_item(self.field_description)
        self.add_item(self.field_inline)

    async def on_submit(self, interaction: discord.Interaction):
        field_title = self.field_title.value.strip()
        field_description = self.field_description.value.strip() if self.field_description.value else None
        if self.field_inline.value.strip() == "True":
            inline = True
        else:
            inline = False

        # Add the new field to the embed
        try:
            await self.bot.get_cog("EmbedProject").add_field_to_embed(interaction.user.id, self.embed_name, field_title, field_description, inline)
            embed = await self.bot.get_cog("EmbedProject").retrieve_embed_data(interaction.user.id, self.embed_name)
            if embed:
                await interaction.response.send_message(embed=embed, view=EmbedEditButtons(self.bot, interaction.user.id, self.embed_name), ephemeral=True)
            else:
                await interaction.response.send_message("Failed to add the field.", ephemeral=True)
        except Exception as e:
            await interaction.response.send_message('Oops! Something went wrong.', ephemeral=True)
            traceback.print_exception(type(e), e, e.__traceback__)


class TitleModal(discord.ui.Modal, title='Edit Title'):
    def __init__(self, bot, user_id, embed_name, update_callback):
        super().__init__()
        self.bot = bot
        self.user_id = user_id
        self.embed_name = embed_name
        self.update_callback = update_callback

        self.new_title = discord.ui.TextInput(
            label='Title',
            style=discord.TextStyle.short,
            placeholder='Your Title here... (Type None to remove)',
            required=False,  # Allow users to submit an empty title
            default=""
        )
        self.add_item(self.new_title)

    async def on_submit(self, interaction: discord.Interaction):
        new_title = self.new_title.value.strip() if self.new_title.value else None
        if new_title == 'None':  # Check if the input is explicitly empty
            new_title = None  # Set to None to indicate removal of the title

        try:
            await self.bot.get_cog("EmbedProject").update_user_embeds(
                self.user_id, self.embed_name, title=new_title
            )
            embed = await self.bot.get_cog("EmbedProject").retrieve_embed_data(self.user_id, self.embed_name)
            if embed:
                await interaction.response.send_message(embed=embed, view=EmbedEditButtons(self.bot, self.user_id, self.embed_name), ephemeral=True)
            else:
                await interaction.response.send_message("Failed to update the title.", ephemeral=True)
        except Exception as e:
            await interaction.response.send_message('Oops! Something went wrong.', ephemeral=True)
            traceback.print_exception(type(e), e, e.__traceback__)

    async def setup(self):
        # Fetch the current title
        current_title = await self.bot.get_cog("EmbedProject").get_embed_property(self.user_id, self.embed_name, "title")
        self.new_title.default = current_title if current_title else ""

class DescriptionModal(discord.ui.Modal, title='Edit Description'):
    def __init__(self, bot, user_id, embed_name, update_callback):
        super().__init__()
        self.bot = bot
        self.user_id = user_id
        self.embed_name = embed_name
        self.update_callback = update_callback

        self.new_description = discord.ui.TextInput(
            label='Description',
            style=discord.TextStyle.long,
            placeholder='Your description here...',
            required=False,  # This field is optional
            default=""
        )
        self.add_item(self.new_description)

    async def on_submit(self, interaction: discord.Interaction):
        new_description = self.new_description.value.strip() if self.new_description.value else None
        if new_description == 'None':  # Check if the input is explicitly empty
            new_description = None  # Set to None to indicate removal of the description
        try:
            await self.bot.get_cog("EmbedProject").update_user_embeds(
                self.user_id, self.embed_name, description=new_description
            )
            embed = await self.bot.get_cog("EmbedProject").retrieve_embed_data(self.user_id, self.embed_name)
            if embed:
                await interaction.response.send_message(embed=embed, view=EmbedEditButtons(self.bot, self.user_id, self.embed_name), ephemeral=True)
            else:
                await interaction.response.send_message("Failed to update the description.", ephemeral=True)
        except Exception as e:
            await interaction.response.send_message('Oops! Something went wrong.', ephemeral=True)
            traceback.print_exception(type(e), e, e.__traceback__)

    async def setup(self):
        # Fetch the current description
        current_description = await self.bot.get_cog("EmbedProject").get_embed_property(self.user_id, self.embed_name, "description")
        self.new_description.default = current_description if current_description else ""

class ColorModal(discord.ui.Modal, title='Edit Color'):
    def __init__(self, bot, user_id, embed_name, update_callback):
        super().__init__()
        self.bot = bot
        self.user_id = user_id
        self.embed_name = embed_name
        self.update_callback = update_callback

        self.new_color = discord.ui.TextInput(
            label='Color',
            style=discord.TextStyle.short,
            placeholder='Enter the new color: Eg. #ffffff',
            required=False,  # This field is optional
            default=""
        )
        self.add_item(self.new_color)

    async def on_submit(self, interaction: discord.Interaction):
        color_input = self.new_color.value.strip('#')
        try:
            # Validate the color format
            color_value = int(color_input, 16) if color_input else 0x2F3136
            await self.bot.get_cog("EmbedProject").update_user_embeds(
                self.user_id, self.embed_name, color=color_value
            )
            embed = await self.bot.get_cog("EmbedProject").retrieve_embed_data(self.user_id, self.embed_name)
            if embed:
                await interaction.response.send_message(embed=embed, view=EmbedEditButtons(self.bot, self.user_id, self.embed_name), ephemeral=True)
            else:
                await interaction.response.send_message("Failed to update the color.", ephemeral=True)
        except ValueError:
            # Handle invalid color format
            await interaction.response.send_message("Invalid color format. Please use a hex format, e.g., #FFFFFF.", ephemeral=True)
        except Exception as e:
            await interaction.response.send_message('Oops! Something went wrong.', ephemeral=True)
            traceback.print_exception(type(e), e, e.__traceback__)

    async def setup(self):
        # Fetch the current color
        current_color = await self.bot.get_cog("EmbedProject").get_embed_property(self.user_id, self.embed_name, "color")
        self.new_color.default = current_color if current_color else ""

class ImageModal(discord.ui.Modal, title='Edit Image'):
    def __init__(self, bot, user_id, embed_name, update_callback):
        super().__init__()
        self.bot = bot
        self.user_id = user_id
        self.embed_name = embed_name
        self.update_callback = update_callback

        self.new_image = discord.ui.TextInput(
            label='Image URL',
            style=discord.TextStyle.short,
            placeholder='Your image URL here...',
            required=False,  # This field is optional
            default=""
        )
        self.add_item(self.new_image)

    async def on_submit(self, interaction: discord.Interaction):
        image_url = self.new_image.value.strip() if self.new_image.value else None
        if image_url == 'None':  # Check if the input is explicitly empty
            image_url = None  # Set to None to indicate removal of the image
        if image_url is not None and not is_valid_url(image_url):
            await interaction.response.send_message("Invalid URL format. Please enter a valid URL.", ephemeral=True)
            return

        try:
            await self.bot.get_cog("EmbedProject").update_user_embeds(
                self.user_id, self.embed_name, image_url=image_url
            )
            embed = await self.bot.get_cog("EmbedProject").retrieve_embed_data(self.user_id, self.embed_name)
            if embed:
                await interaction.response.send_message(embed=embed, view=EmbedEditButtons(self.bot, self.user_id, self.embed_name), ephemeral=True)
            else:
                await interaction.response.send_message("Failed to update the image.", ephemeral=True)
        except Exception as e:
            await interaction.response.send_message('Oops! Something went wrong.', ephemeral=True)
            traceback.print_exception(type(e), e, e.__traceback__)

    async def setup(self):
        # Fetch the current image URL
        current_image = await self.bot.get_cog("EmbedProject").get_embed_property(self.user_id, self.embed_name, "image_url")
        self.new_image.default = current_image if current_image else ""

class ThumbnailModal(discord.ui.Modal, title='Edit Thumbnail'):
    def __init__(self, bot, user_id, embed_name, update_callback):
        super().__init__()
        self.bot = bot
        self.user_id = user_id
        self.embed_name = embed_name
        self.update_callback = update_callback

        self.new_thumbnail = discord.ui.TextInput(
            label='Thumbnail URL',
            style=discord.TextStyle.short,
            placeholder='Your thumbnail URL here...',
            required=False,  # This field is optional
            default=""
        )
        self.add_item(self.new_thumbnail)

    async def on_submit(self, interaction: discord.Interaction):
        thumbnail_url = self.new_thumbnail.value.strip() if self.new_thumbnail.value else None
        if thumbnail_url == 'None':  # Check if the input is explicitly empty
            thumbnail_url = None  # Set to None to indicate removal of the thumbnail
        if thumbnail_url is not None and not is_valid_url(thumbnail_url):
            await interaction.response.send_message("Invalid URL format. Please enter a valid URL.", ephemeral=True)
            return

        try:
            await self.bot.get_cog("EmbedProject").update_user_embeds(
                self.user_id, self.embed_name, thumbnail_url=thumbnail_url
            )
            embed = await self.bot.get_cog("EmbedProject").retrieve_embed_data(self.user_id, self.embed_name)
            if embed:
                await interaction.response.send_message(embed=embed, view=EmbedEditButtons(self.bot, self.user_id, self.embed_name), ephemeral=True)
            else:
                await interaction.response.send_message("Failed to update the thumbnail.", ephemeral=True)
        except Exception as e:
            await interaction.response.send_message('Oops! Something went wrong.', ephemeral=True)
            traceback.print_exception(type(e), e, e.__traceback__)

    async def setup(self):
        # Fetch the current thumbnail URL
        current_thumbnail = await self.bot.get_cog("EmbedProject").get_embed_property(self.user_id, self.embed_name, "thumbnail_url")
        self.new_thumbnail.default = current_thumbnail if current_thumbnail else ""

class FooterModal(discord.ui.Modal, title='Edit Footer'):
    def __init__(self, bot, user_id, embed_name, update_callback):
        super().__init__()
        self.bot = bot
        self.user_id = user_id
        self.embed_name = embed_name
        self.update_callback = update_callback

        self.footer_text = discord.ui.TextInput(
            label='Footer Text',
            style=discord.TextStyle.short,
            placeholder='Enter footer text here...',
            required=False,  # This field is optional
            default=""
        )
        self.add_item(self.footer_text)

        self.footer_icon_url = discord.ui.TextInput(
            label='Footer Icon URL',
            style=discord.TextStyle.short,
            placeholder='Enter footer icon URL here... (optional)',
            required=False,  # This field is optional
            default=""
        )
        self.add_item(self.footer_icon_url)

    async def on_submit(self, interaction: discord.Interaction):
        footer_text = self.footer_text.value.strip()
        footer_icon_url = self.footer_icon_url.value.strip() if self.footer_icon_url.value else None

        if footer_text.lower() == 'none':
            footer_text = None
            footer_icon_url = None  # Remove the icon URL as well since text is required for the icon

        if footer_text and footer_icon_url and not is_valid_url(footer_icon_url):
            await interaction.response.send_message("Invalid URL format for the footer icon. Please enter a valid URL.", ephemeral=True)
            return

        try:
            await self.bot.get_cog("EmbedProject").update_user_embeds(
                self.user_id, self.embed_name,
                footer_text=footer_text,
                footer_icon_url=footer_icon_url
            )
            embed = await self.bot.get_cog("EmbedProject").retrieve_embed_data(self.user_id, self.embed_name)
            if embed:
                await interaction.response.send_message(embed=embed, view=EmbedEditButtons(self.bot, self.user_id, self.embed_name), ephemeral=True)
            else:
                await interaction.response.send_message("Failed to update the footer.", ephemeral=True)
        except Exception as e:
            await interaction.response.send_message('Oops! Something went wrong.', ephemeral=True)
            traceback.print_exception(type(e), e, e.__traceback__)

    async def setup(self):
        # Fetch the current footer text and icon URL
        current_footer_text = await self.bot.get_cog("EmbedProject").get_embed_property(self.user_id, self.embed_name, "footer_text")
        current_footer_icon = await self.bot.get_cog("EmbedProject").get_embed_property(self.user_id, self.embed_name, "footer_icon_url")
        self.footer_text.default = current_footer_text if current_footer_text else ""
        self.footer_icon_url.default = current_footer_icon if current_footer_icon else ""

class AuthorModal(discord.ui.Modal, title='Edit Author'):
    def __init__(self, bot, user_id, embed_name, update_callback):
        super().__init__()
        self.bot = bot
        self.user_id = user_id
        self.embed_name = embed_name
        self.update_callback = update_callback

        self.author_text = discord.ui.TextInput(
            label='Author Text',
            style=discord.TextStyle.short,
            placeholder='Enter author text here...',
            required=False,  # This field is optional
            default=""
        )
        self.add_item(self.author_text)

        self.author_icon_url = discord.ui.TextInput(
            label='Author Icon URL',
            style=discord.TextStyle.short,
            placeholder='Enter author icon URL here... (optional)',
            required=False,  # This field is optional
            default=""
        )
        self.add_item(self.author_icon_url)

    async def on_submit(self, interaction: discord.Interaction):
        author_text = self.author_text.value.strip()
        author_icon_url = self.author_icon_url.value.strip() if self.author_icon_url.value else None

        if author_icon_url and not is_valid_url(author_icon_url):
            await interaction.response.send_message("Invalid URL format for the author icon. Please enter a valid URL.", ephemoral=True)
            return

        try:
            await self.bot.get_cog("EmbedProject").update_user_embeds(
                self.user_id, self.embed_name,
                author_text=author_text,
                author_icon_url=author_icon_url
            )
            embed = await self.bot.get_cog("EmbedProject").retrieve_embed_data(self.user_id, self.embed_name)
            if embed:
                await interaction.response.send_message(embed=embed, view=EmbedEditButtons(self.bot, self.user_id, self.embed_name), ephemeral=True)
            else:
                await interaction.response.send_message("Failed to update the author.", ephemeral=True)
        except Exception as e:
            await interaction.response.send_message('Oops! Something went wrong.', ephemeral=True)
            traceback.print_exception(type(e), e, e.__traceback__)

    async def setup(self):
        # Fetch the current author text and icon URL
        current_author_text = await self.bot.get_cog("EmbedProject").get_embed_property(self.user_id, self.embed_name, "author_text")
        current_author_icon = await self.bot.get_cog("EmbedProject").get_embed_property(self.user_id, self.embed_name, "author_icon_url")
        self.author_text.default = current_author_text if current_author_text else ""
        self.author_icon_url.default = current_author_icon if current_author_icon else ""

class DynamicButtonView(discord.ui.View):
    def __init__(self, bot):
        super().__init__(timeout=None)  # No timeout for buttons
        self.bot = bot
        self.bot.loop.create_task(self.load_all_buttons())

    async def load_all_buttons(self):
        try:
            async with aiosqlite.connect('db/buttons.db') as db:
                async with db.execute("SELECT DISTINCT embed_name FROM buttons") as cursor:
                    embed_names = await cursor.fetchall()
                    for embed_name in embed_names:
                        await self.load_buttons_for_embed(embed_name[0])
        except Exception as e:
            print(f"Failed to load buttons: {str(e)}")

    async def load_buttons_for_embed(self, embed_name):
        async with aiosqlite.connect('db/buttons.db') as db:
            async with db.execute("SELECT * FROM buttons WHERE embed_name = ?", (embed_name,)) as cursor:
                button_configs = await cursor.fetchall()
                for button_config in button_configs:
                    button_data = dict(zip([description[0] for description in cursor.description], button_config))
                    # Convert custom_id to string
                    button_data['custom_id'] = str(button_data['custom_id'])
                    if button_data['style'].lower() == 'link' and button_data.get('link'):
                        # Create a link button directly
                        button = discord.ui.Button(label=button_data['label'], style=discord.ButtonStyle.link, url=button_data['link'])
                    else:
                        # Create a regular button that can trigger interactions
                        button = DynamicButton(button_data, self.bot)
                    self.add_item(button)

class DynamicButton(discord.ui.Button):
    def __init__(self, config, bot):
        self.bot = bot
        style = self.map_style(config['style'])
        url = config['link'] if style == discord.ButtonStyle.link else None
        emoji = config.get('emoji')  # Retrieve the emoji from the configuration
        super().__init__(label=config['label'], style=style, url=url, custom_id=config['custom_id'], emoji=emoji)
        self.config = config

    @staticmethod
    def map_style(style_str):
        style_map = {
            "primary": discord.ButtonStyle.primary,
            "secondary": discord.ButtonStyle.secondary,
            "success": discord.ButtonStyle.success,
            "danger": discord.ButtonStyle.danger,
            "link": discord.ButtonStyle.link
        }
        return style_map.get(style_str.lower(), discord.ButtonStyle.secondary)

    async def callback(self, interaction: discord.Interaction):
        user = interaction.user
        guild = interaction.guild
        creator_user_id = self.config['user_id']
        embed_name = self.config.get('send_embed')
        embed_data = None
        if embed_name:
            embed_data = await self.bot.get_cog("EmbedProject").retrieve_embed_data(creator_user_id, embed_name, include_view=True)
        if self.config.get('role_menu_name'):
            # Handle role menu button
            roles_cog = self.bot.get_cog("Roles")
            if roles_cog:
                roles, settings = await roles_cog.fetch_roles_from_db(interaction, self.config['role_menu_name'])
                max_values = settings['max_values']
                print(max_values)
                if max_values <= 0:
                    # If max_values is 0 or negative, set it to the number of roles in the menu
                    max_values = len(roles)
                    async with aiosqlite.connect("db/roles.db") as db:
                        await db.execute("UPDATE role_menus SET max_values = ? WHERE guild_id = ? AND menu_name = ?", (max_values, interaction.guild.id, self.config['role_menu_name']))
                        await db.commit()
                
                if roles:
                    view = RoleMenuView(roles, settings['placeholder'], settings['min_values'], max_values, interaction.user)
                    await interaction.response.send_message(f"Select a role from the {self.config['role_menu_name']} menu:", view=view, ephemeral=True)
                else:
                    await interaction.response.send_message("No roles found for this menu.", ephemeral=True)
            return
        if self.config.get('role_to_give'):
            role_id = int(self.config['role_to_give'])
            role = guild.get_role(role_id)
            if not role:
                return await interaction.response.send_message("This role does not exist in this server. The button may be configured for a different server.", ephemeral=True)

            if role in user.roles:
                await user.remove_roles(role)
                return await interaction.response.send_message(f"Removed the role {role.name} from you.", ephemeral=True)
            else:
                await user.add_roles(role)
                return await interaction.response.send_message(f"Given you the role {role.name}.", ephemeral=True)

        if self.config.get('custom_message'):
            if embed_data:
                embed, view = embed_data
                await interaction.response.send_message(self.config['custom_message'], embed=embed, view=view, ephemeral=True)
            else:
                await interaction.response.send_message(self.config['custom_message'], ephemeral=True)
        elif embed_data:
            embed, view = embed_data
            await interaction.response.send_message(embed=embed, view=view, ephemeral=True)
        else:
            await interaction.response.send_message("No embed found with that name.", ephemeral=True)

class EmbedProject(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.db_path = "db/embeds.db"
        self.bot.loop.create_task(self.setup_db())
    
    embed = discord.app_commands.Group(name="embed", description="Commands to manage or create embeds")
    async def setup_db(self):
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute("""
                CREATE TABLE IF NOT EXISTS user_embeds (
                    user_id INTEGER,
                    embed_name TEXT,
                    title TEXT,
                    description TEXT,
                    color INTEGER,
                    footer_icon_url TEXT,
                    footer_text TEXT,
                    author_icon_url TEXT,
                    author_text TEXT,
                    thumbnail_url TEXT,
                    image_url TEXT,
                    PRIMARY KEY (user_id, embed_name)
                )
            """)
            await db.execute("""
                CREATE TABLE IF NOT EXISTS embed_fields (
                    user_id INTEGER,
                    embed_name TEXT,
                    title TEXT,
                    description TEXT,
                    inline BOOLEAN,
                    field_id INTEGER,
                    FOREIGN KEY (user_id, embed_name) REFERENCES user_embeds(user_id, embed_name) ON DELETE CASCADE
                )
            """)
            await db.commit()

    async def save_user_embeds(self, user_id: int, embed_name: str, **kwargs):
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute("""
                INSERT INTO user_embeds (user_id, embed_name, title, description, color, footer_icon_url, footer_text, author_icon_url, author_text, thumbnail_url, image_url)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(user_id, embed_name) DO UPDATE SET
                title = excluded.title,
                description = excluded.description,
                color = excluded.color,
                footer_icon_url = excluded.footer_icon_url,
                footer_text = excluded.footer_text,
                author_icon_url = excluded.author_icon_url,
                author_text = excluded.author_text,
                thumbnail_url = excluded.thumbnail_url,
                image_url = excluded.image_url
            """, (user_id, embed_name, kwargs.get('title'), kwargs.get('description'), kwargs.get('color'),
                kwargs.get('footer_icon_url'), kwargs.get('footer_text'), kwargs.get('author_icon_url'), kwargs.get('author_text'), kwargs.get('thumbnail_url'), kwargs.get('image_url')))
            await db.commit()

    async def retrieve_embed_data(self, user_id: int, embed_name: str, include_view=False):
        async with aiosqlite.connect(self.db_path) as db:
            async with db.execute("SELECT * FROM user_embeds WHERE user_id = ? AND embed_name = ?", (user_id, embed_name)) as cursor:
                row = await cursor.fetchone()
                if not row:
                    print(f"No embed found with the name '{embed_name}' for the user with ID {user_id}.")
                    return None
                
                columns = [description[0] for description in cursor.description]
                data = dict(zip(columns, row))
                
                # Always creates an embed with at least a description
                embed = discord.Embed(
                    title=data.get("title") or "",
                    description=data.get("description") or f"This embed '{embed_name}' is empty. Add some properties to it.",
                    color=data.get("color") or 0
                )
                
                if data.get("footer_text"):
                    embed.set_footer(text=data["footer_text"], icon_url=data.get("footer_icon_url"))
                if data.get("author_text"):
                    embed.set_author(name=data["author_text"], icon_url=data.get("author_icon_url"))
                if data.get("thumbnail_url"):
                    embed.set_thumbnail(url=data["thumbnail_url"])
                if data.get("image_url"):
                    embed.set_image(url=data["image_url"])

            # Retrieve fields for the embed
            async with db.execute("SELECT field_id, title, description, inline FROM embed_fields WHERE user_id = ? AND embed_name = ? ORDER BY field_id", (user_id, embed_name)) as field_cursor:
                fields = await field_cursor.fetchall()
                for field in fields:
                    embed.add_field(name=field[1] or "\u200b", value=field[2] or "\u200b", inline=bool(field[3]))

        if include_view:
            # Retrieve button configurations for this embed that belong to the user
            async with aiosqlite.connect('db/buttons.db') as button_db:
                async with button_db.execute("SELECT * FROM buttons WHERE user_id = ? AND embed_name = ?", (user_id, embed_name)) as button_cursor:
                    buttons = await button_cursor.fetchall()
                    view = discord.ui.View()
                    for button in buttons:
                        button_data = dict(zip([description[0] for description in button_cursor.description], button))
                        # Convert custom_id to string
                        button_data['custom_id'] = str(button_data['custom_id'])
                        view.add_item(DynamicButton(button_data, self.bot))
            return embed, view
        else:
            return embed
                
    async def delete_button_info_db(self, user_id: int, custom_id: str):
        async with aiosqlite.connect('db/buttons.db') as db:
            await db.execute("DELETE FROM buttons WHERE custom_id = ? AND user_id = ?", (custom_id, user_id))
            await db.commit()
            if db.total_changes > 0:
                return True, "Button deleted successfully."
            else:
                return False, "No button found with the provided ID or you do not own this button."
            
    async def get_embed_property(self, user_id: int, embed_name: str, property_name: str):
        async with aiosqlite.connect(self.db_path) as db:
            async with db.execute(f"SELECT {property_name} FROM user_embeds WHERE user_id = ? AND embed_name = ?", (user_id, embed_name)) as cursor:
                result = await cursor.fetchone()
                if result:
                    return result[0]
                return None

    async def remove_field_from_embed(self, user_id, embed_name, field_id):
        async with aiosqlite.connect(self.db_path) as db:
            # First, delete the specified field
            await db.execute("DELETE FROM embed_fields WHERE user_id = ? AND embed_name = ? AND field_id = ?", (user_id, embed_name, field_id))
            
            # Fetch all remaining fields for this embed, ordered by their current field_id
            async with db.execute("SELECT field_id FROM embed_fields WHERE user_id = ? AND embed_name = ? ORDER BY field_id", (user_id, embed_name)) as cursor:
                remaining_fields = await cursor.fetchall()
            
            # Update the field_ids to ensure they are consecutive
            for new_id, (old_id,) in enumerate(remaining_fields, start=1):
                await db.execute("""
                    UPDATE embed_fields
                    SET field_id = ?
                    WHERE user_id = ? AND embed_name = ? AND field_id = ?
                """, (new_id, user_id, embed_name, old_id))
            
            await db.commit()
    async def get_embed_fields(self, user_id: int, embed_name: str):
        async with aiosqlite.connect(self.db_path) as db:
            async with db.execute("""
                SELECT field_id, title, description, inline 
                FROM embed_fields 
                WHERE user_id = ? AND embed_name = ? 
                ORDER BY field_id
            """, (user_id, embed_name)) as cursor:
                fields = await cursor.fetchall()
        
        return [
            {
                'id': field[0],
                'name': field[1],
                'value': field[2],
                'inline': bool(field[3])
            }
            for field in fields
        ]
    async def add_field_to_embed(self, user_id: int, embed_name: str, title: str, description: str, inline: bool = False):
        async with aiosqlite.connect(self.db_path) as db:
            # Get the next available field_id
            async with db.execute("SELECT MAX(field_id) FROM embed_fields WHERE user_id = ? AND embed_name = ?", (user_id, embed_name)) as cursor:
                result = await cursor.fetchone()
                field_id = (result[0] or 0) + 1

            await db.execute("""
                INSERT INTO embed_fields (user_id, embed_name, field_id, title, description, inline)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (user_id, embed_name, field_id, title, description, int(inline)))
            await db.commit()
                
    async def add_button_info_db(self, user_id, embed_name, button_label, button_style, link=None, emoji=None, role_to_give=None, send_embed=None, custom_message=None, guild_id=None, role_menu_name=None):
        async with aiosqlite.connect('db/buttons.db') as db:
            await db.execute("""
                CREATE TABLE IF NOT EXISTS buttons (
                    custom_id INTEGER PRIMARY KEY,
                    user_id INTEGER,
                    embed_name TEXT,
                    label TEXT,
                    style TEXT,
                    link TEXT,
                    emoji TEXT,
                    role_to_give TEXT,
                    send_embed TEXT,
                    custom_message TEXT,
                    guild_id INTEGER,
                    role_menu_name TEXT
                )
            """)
            cursor = await db.execute("SELECT MAX(custom_id) FROM buttons")
            result = await cursor.fetchone()
            last_id = result[0] if result[0] else 0
            new_id = last_id + 1
            custom_id = f"{new_id:06d}"
            await db.execute("""
                INSERT INTO buttons (custom_id, user_id, embed_name, label, style, link, emoji, role_to_give, send_embed, custom_message, guild_id, role_menu_name)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (custom_id, user_id, embed_name, button_label, button_style, link, emoji, role_to_give, send_embed, custom_message, guild_id, role_menu_name))
            await db.commit()
            return custom_id
        
    async def update_field_in_embed(self, user_id, embed_name, field_id, new_title, new_text):
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute("""
                UPDATE embed_fields
                SET title = ?, description = ?
                WHERE user_id = ? AND embed_name = ? AND field_id = ?
            """, (new_title, new_text, user_id, embed_name, field_id))
            await db.commit()
            return db.total_changes > 0
        
    async def update_user_embeds(self, user_id: int, embed_name: str, **kwargs):
        set_clause = ", ".join([f"{key} = :{key}" for key in kwargs.keys()])
        params = {**kwargs, "user_id": user_id, "embed_name": embed_name}
        
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute(f"""
                UPDATE user_embeds
                SET {set_clause}
                WHERE user_id = :user_id AND embed_name = :embed_name
            """, params)
            await db.commit()

    async def delete_buttons_for_embed_db(self, user_id: int, embed_name: str):
        async with aiosqlite.connect('db/buttons.db') as db:
            await db.execute("DELETE FROM buttons WHERE user_id = ? AND embed_name = ?", (user_id, embed_name))
            await db.commit()
            if db.total_changes > 0:
                return True, "Buttons deleted successfully."
            else:
                return False, "No buttons found for this embed."
    
    @embed.command(name="builder", description="Create or modify an existing embed")
    @app_commands.describe(embed_name="Name of the embed to edit")
    async def embed_builder(self, interaction: discord.Interaction, embed_name: str):
        embed = await self.retrieve_embed_data(interaction.user.id, embed_name)
        view = EmbedbuilderButtons(self.bot, interaction.user.id, embed_name)
        
        if embed:
            # Existing embed
            await interaction.response.send_message(f"<:5068file:1233764689071046687> Embed Builder: {embed_name}\n-# Use the buttons below to modify your embed.",embed=embed, view=view, ephemeral=True)
        else:
            # New embed
            default_title = f"<:5068file:1233764689071046687> New Embed Created: {embed_name}"
            default_description = (
                "Welcome to the Embed Builder! Here's how to use it:\n\n"
                "<a:pencil_cc:1235842878740238347> **Edit Embed**:\n"
                "Modify title, description, color, images, footer, and author.\n\n"
                "<:plus:1235848647531298876> **Add Button**:\n"
                "Create interactive buttons for your embed.\n\n"
                "<:delete:1233761545754771546> **Remove Button**:\n"
                "Delete unwanted buttons from your embed.\n\n"
                "<a:fire:1235847103041900554> **Reveal Embed**:\n"
                "Preview your embed as it will appear to users.\n\n"
                "<:del:1235849127179452468> **Delete Embed**:\n"
                "Permanently remove this embed if needed.\n\n"
                "Start customizing your embed now!\n\n"
                "<a:83888settingsanimation:1233771395415015524> **Your New Embed**\n"
                "-# This is your new embed. Use the buttons below to modify it."
            )
            default_color = 0x2F3136
            await self.save_user_embeds(
                interaction.user.id, embed_name,
                title=default_title, description=default_description, color=default_color
            )
            new_embed = await self.retrieve_embed_data(interaction.user.id, embed_name)
            if new_embed:
                await interaction.response.send_message(embed=new_embed, view=view, ephemeral=True)
            else:
                error_embed = discord.Embed(
                    title="<:1001timeout:1233770920099844227> Error",
                    description="Failed to create a new embed.",
                    color=0xFF0000
                )
                error_embed.set_footer(text=f"Requested by {interaction.user}", icon_url=interaction.user.avatar.url)
                error_embed.timestamp = discord.utils.utcnow()
                await interaction.response.send_message(embed=error_embed, ephemeral=True)
    
    @app_commands.command(name="through-webhook", description="Send an embed through a webhook")
    @app_commands.describe(
        embed_name="Name of the embed to send",
        webhook_url="URL of the webhook to use (optional, can't send buttoned embeds)",
        channel="Channel to send the embed to (optional, defaults to current channel)"
    )
    async def send_through_webhook(
        self, 
        interaction: Interaction, 
        embed_name: str, 
        webhook_url: Optional[str] = None, 
        channel: Optional[TextChannel] = None
    ):
        if webhook_url and channel:
            error_embed = discord.Embed(
                title="<:1001timeout:1233770920099844227> Error",
                description="Please provide either a webhook URL or a channel, not both.",
                color=0xFF0000
            )
            error_embed.set_footer(text=f"Requested by {interaction.user}", icon_url=interaction.user.avatar.url)
            error_embed.timestamp = discord.utils.utcnow()
            await interaction.response.send_message(embed=error_embed, ephemeral=True)
            return

        channel = channel or interaction.channel
        
        embed_data = await self.retrieve_embed_data(interaction.user.id, embed_name, include_view=True)
        if not embed_data:
            error_embed = discord.Embed(
                title="<:1001timeout:1233770920099844227> Error",
                description=f"No embed found with the name '{embed_name}'.",
                color=0xFF0000
            )
            error_embed.set_footer(text=f"Requested by {interaction.user}", icon_url=interaction.user.avatar.url)
            error_embed.timestamp = discord.utils.utcnow()
            await interaction.response.send_message(embed=error_embed, ephemeral=True)
            return

        embed, view = embed_data

        try:
            if webhook_url:
                if view.children:
                    warning_embed = discord.Embed(
                        title="<:8355moon:1233771385839681566> Warning",
                        description="Buttons cannot be sent through a webhook URL. They will be omitted.",
                        color=0xFFA500
                    )
                    warning_embed.set_footer(text=f"Requested by {interaction.user}", icon_url=interaction.user.avatar.url)
                    warning_embed.timestamp = discord.utils.utcnow()
                    await interaction.response.send_message(embed=warning_embed, ephemeral=True)
                    view = None
                async with aiohttp.ClientSession() as session:
                    webhook = Webhook.from_url(webhook_url, session=session)
                    await webhook.send(embed=embed, view=view)
            else:
                webhooks = await channel.webhooks()
                webhook = next((wh for wh in webhooks if wh.user == interaction.client.user), None)
                if not webhook:
                    error_embed = discord.Embed(
                        title="<:1001timeout:1233770920099844227> Error",
                        description=f"No webhook found in the specified channel. Please use the `/create-webhook` command first.",
                        color=0xFF0000
                    )
                    error_embed.set_footer(text=f"Requested by {interaction.user}", icon_url=interaction.user.avatar.url)
                    error_embed.timestamp = discord.utils.utcnow()
                    await interaction.response.send_message(embed=error_embed, ephemeral=True)
                    return
                await webhook.send(embed=embed, view=view)

            success_embed = discord.Embed(
                title="<a:fire:1235847103041900554> Success",
                description="Message sent successfully through the webhook.",
                color=0x2F3136
            )
            success_embed.set_footer(text=f"Requested by {interaction.user}", icon_url=interaction.user.avatar.url)
            success_embed.timestamp = discord.utils.utcnow()
            await interaction.response.send_message(embed=success_embed, ephemeral=True)
        except HTTPException as e:
            error_embed = discord.Embed(
                title="<:1001timeout:1233770920099844227> Error",
                description=f"An error occurred: {str(e)}",
                color=0xFF0000
            )
            error_embed.set_footer(text=f"Requested by {interaction.user}", icon_url=interaction.user.avatar.url)
            error_embed.timestamp = discord.utils.utcnow()
            await interaction.response.send_message(embed=error_embed, ephemeral=True)

    @app_commands.command(name="create-webhook", description="Create a webhook in the specified channel")
    @app_commands.describe(
        channel="The channel to create the webhook in (optional, defaults to current channel)",
        avatar="URL for the webhook's avatar (optional)",
        name="Name for the webhook (optional, defaults to bot's name)"
    )
    async def create_webhook(
        self, 
        interaction: Interaction, 
        channel: Optional[TextChannel] = None, 
        avatar: Optional[str] = None, 
        name: Optional[str] = None
    ):
        channel = channel or interaction.channel
        name = name or interaction.client.user.name

        if not channel.permissions_for(interaction.guild.me).manage_webhooks:
            error_embed = discord.Embed(
                title="<:1001timeout:1233770920099844227> Error",
                description="I don't have permission to manage webhooks in this channel.",
                color=0xFF0000
            )
            error_embed.set_footer(text=f"Requested by {interaction.user}", icon_url=interaction.user.avatar.url)
            error_embed.timestamp = discord.utils.utcnow()
            await interaction.response.send_message(embed=error_embed, ephemeral=True)
            return

        try:
            avatar_bytes = None
            if avatar:
                async with aiohttp.ClientSession() as session:
                    async with session.get(avatar) as resp:
                        if resp.status == 200:
                            avatar_bytes = await resp.read()
                        else:
                            error_embed = discord.Embed(
                                title="<:1001timeout:1233770920099844227> Error",
                                description="Failed to fetch the avatar image.",
                                color=0xFF0000
                            )
                            error_embed.set_footer(text=f"Requested by {interaction.user}", icon_url=interaction.user.avatar.url)
                            error_embed.timestamp = discord.utils.utcnow()
                            await interaction.response.send_message(embed=error_embed, ephemeral=True)
                            return

            webhook = await channel.create_webhook(name=name, avatar=avatar_bytes)
            success_embed = discord.Embed(
                title="<a:fire:1235847103041900554> Webhook Created",
                description=f"Webhook created successfully!\nURL: {webhook.url}",
                color=0x2F3136
            )
            success_embed.set_footer(text=f"Requested by {interaction.user}", icon_url=interaction.user.avatar.url)
            success_embed.timestamp = discord.utils.utcnow()
            await interaction.response.send_message(embed=success_embed, ephemeral=True)
        except HTTPException as e:
            error_embed = discord.Embed(
                title="<:1001timeout:1233770920099844227> Error",
                description=f"Failed to create webhook: {str(e)}",
                color=0xFF0000
            )
            error_embed.set_footer(text=f"Requested by {interaction.user}", icon_url=interaction.user.avatar.url)
            error_embed.timestamp = discord.utils.utcnow()
            await interaction.response.send_message(embed=error_embed, ephemeral=True)

    async def fetch_user_buttons(self, user_id):
        async with aiosqlite.connect('db/buttons.db') as db:
            async with db.execute("SELECT label, custom_id, embed_name FROM buttons WHERE user_id = ?", (user_id,)) as cursor:
                buttons = await cursor.fetchall()
                if not buttons:
                    return None, "No buttons found for the user."
            user_buttons = [f"<:9177neonredarrowright:1240180166089769000> **{button[0]}**\n> **ID:** `{button[1]}`, **Embed:** `{button[2]}`" for button in buttons]
            return user_buttons, None

    @embed.command(name="buttons", description="View your embed buttons")
    async def my_buttons(self, interaction: discord.Interaction):
        user_id = interaction.user.id
        user_buttons, error_message = await self.fetch_user_buttons(user_id)

        if error_message:
            error_embed = discord.Embed(
                title="<:1001timeout:1233770920099844227> Error",
                description=error_message,
                color=0xFF0000
            )
            error_embed.set_footer(text=f"Requested by {interaction.user}", icon_url=interaction.user.avatar.url)
            error_embed.timestamp = discord.utils.utcnow()
            await interaction.response.send_message(embed=error_embed, ephemeral=True)
            return

        if user_buttons:
            description = "\n\n".join(user_buttons)
            embed = discord.Embed(
                title="<a:83888settingsanimation:1233771395415015524> Your Buttons",
                description=description,
                color=0x2F3136
            )
            embed.set_footer(text=f"Requested by {interaction.user}", icon_url=interaction.user.avatar.url)
            embed.timestamp = discord.utils.utcnow()
            await interaction.response.send_message(embed=embed, ephemeral=True)
        else:
            no_buttons_embed = discord.Embed(
                title="<:1001timeout:1233770920099844227> No Buttons",
                description="You have not created any buttons.",
                color=0xFF0000
            )
            no_buttons_embed.set_footer(text=f"Requested by {interaction.user}", icon_url=interaction.user.avatar.url)
            no_buttons_embed.timestamp = discord.utils.utcnow()
            await interaction.response.send_message(embed=no_buttons_embed, ephemeral=True)

    @embed.command(name="delete-button", description="Delete a button from an embed")
    @app_commands.describe(custom_id="The custom ID of the button to delete")
    async def delete_button(self, interaction: discord.Interaction, custom_id: str):
        user_id = interaction.user.id
        success, message = await self.delete_button_info_db(user_id, custom_id)
        if not success:
            if "not found" in message:
                message = f"No button found with ID: {custom_id}. Please check the ID and try again."
            elif "do not own" in message:
                message = "You do not have permission to delete this button."
            error_embed = discord.Embed(
                title="<:1001timeout:1233770920099844227> Error",
                description=message,
                color=0xFF0000
            )
        else:
            error_embed = discord.Embed(
                title="<a:fire:1235847103041900554> Success",
                description=message,
                color=0x2F3136
            )
        error_embed.set_footer(text=f"Requested by {interaction.user}", icon_url=interaction.user.avatar.url)
        error_embed.timestamp = discord.utils.utcnow()
        await interaction.response.send_message(embed=error_embed, ephemeral=True)

    quick = discord.app_commands.Group(name="quick", description="Quickly create an embed.")
    @quick.command(name="embed", description="Quickly create an embed!")
    @app_commands.describe(
        embed_name="Name of the embed",
        title="Title of the embed",
        description="Description of the embed",
        color="Color of the embed in hex",
        footer_icon_url="URL of the footer icon",
        footer_text="Text for the footer",
        author_icon_url="URL of the author icon",
        author_text="Text for the author",
        thumbnail_url="URL of the thumbnail",
        image_url="URL of the image"
    )
    async def quick_embed(
        self,
        interaction: discord.Interaction,
        embed_name: str,
        title: str = "This is Title",
        description: str = "This is description",
        color: str = "000000",
        footer_icon_url: str = None,
        footer_text: str = None,
        author_icon_url: str = None,
        author_text: str = None,
        thumbnail_url: str = None,
        image_url: str = None
    ):
        # Convert color from hex to int
        try:
            color = int(color.strip("#"), 16)
        except ValueError:
            error_embed = discord.Embed(
                title="<:1001timeout:1233770920099844227> Invalid Color Format",
                description="Please use hex format, e.g., `#FFFFFF`.",
                color=0xFF0000
            )
            error_embed.set_footer(text=f"Requested by {interaction.user}", icon_url=interaction.user.avatar.url)
            error_embed.timestamp = discord.utils.utcnow()
            await interaction.response.send_message(embed=error_embed, ephemeral=True)
            return

        # Validate URLs
        def validate_url(url):
            return url and (url.startswith("http://") or url.startswith("https://"))

        invalid_urls = [f"`{field}`" for field, url in [
            ("Footer Icon", footer_icon_url),
            ("Author Icon", author_icon_url),
            ("Thumbnail", thumbnail_url),
            ("Image", image_url)
        ] if url and not validate_url(url)]

        if invalid_urls:
            error_embed = discord.Embed(
                title="<:1001timeout:1233770920099844227> Invalid URL(s)",
                description=f"The following URL(s) are invalid:\n{', '.join(invalid_urls)}\n\nURLs must start with `http://` or `https://`",
                color=0xFF0000
            )
            error_embed.set_footer(text=f"Requested by {interaction.user}", icon_url=interaction.user.avatar.url)
            error_embed.timestamp = discord.utils.utcnow()
            await interaction.response.send_message(embed=error_embed, ephemeral=True)
            return

        # Save and retrieve embed data
        await self.save_user_embeds(
            interaction.user.id, embed_name,
            title=title, description=description, color=color,
            footer_icon_url=footer_icon_url, footer_text=footer_text,
            author_icon_url=author_icon_url, author_text=author_text,
            thumbnail_url=thumbnail_url, image_url=image_url
        )
        embed = await self.retrieve_embed_data(interaction.user.id, embed_name)
        if embed:
            success_embed = discord.Embed(
                title="<a:fire:1235847103041900554> Embed Created Successfully",
                description=f"Your embed **{embed_name}** has been created. Here's a preview:",
                color=0x2F3136
            )
            success_embed.set_footer(text=f"Requested by {interaction.user}", icon_url=interaction.user.avatar.url)
            success_embed.timestamp = discord.utils.utcnow()
            await interaction.response.send_message(embeds=[success_embed, embed], ephemeral=True)
        else:
            error_embed = discord.Embed(
                title="<:1001timeout:1233770920099844227> Embed Creation Failed",
                description="Failed to create or retrieve the embed.",
                color=0xFF0000
            )
            error_embed.set_footer(text=f"Requested by {interaction.user}", icon_url=interaction.user.avatar.url)
            error_embed.timestamp = discord.utils.utcnow()
            await interaction.response.send_message(embed=error_embed, ephemeral=True)

    @commands.hybrid_command(name="embed-edit", description="Edit a specific property of an existing embed")
    @app_commands.describe(
        embed_name="Name of the embed to edit",
        property="Property of the embed to edit",
        value="New value for the property"
    )
    @app_commands.choices(property=[
        app_commands.Choice(name="title", value="title"),
        app_commands.Choice(name="description", value="description"),
        app_commands.Choice(name="color", value="color"),
        app_commands.Choice(name="footer_icon_url", value="footer_icon_url"),
        app_commands.Choice(name="footer_text", value="footer_text"),
        app_commands.Choice(name="author_icon_url", value="author_icon_url"),
        app_commands.Choice(name="author_text", value="author_text"),
        app_commands.Choice(name="thumbnail_url", value="thumbnail_url"),
        app_commands.Choice(name="image_url", value="image_url")
    ])
    async def edit_embed(self, ctx: commands.Context, embed_name: str, property: str, *, value: str):
        if value.lower() == 'none':
            value = None

        if property in ["footer_icon_url", "author_icon_url", "thumbnail_url", "image_url"] and value:
            if not (value.startswith("http://") or value.startswith("https://")):
                error_embed = discord.Embed(
                    title="<:1001timeout:1233770920099844227> Invalid URL",
                    description=f"Invalid URL provided for `{property}`. URLs must start with `http://` or `https://`",
                    color=0xFF0000
                )
                error_embed.set_footer(text=f"Requested by {ctx.author}", icon_url=ctx.author.avatar.url)
                error_embed.timestamp = discord.utils.utcnow()
                await ctx.send(embed=error_embed, ephemeral=True)
                return

        if property == "color" and value:
            try:
                value = int(value.strip("#"), 16)
            except ValueError:
                error_embed = discord.Embed(
                    title="<:1001timeout:1233770920099844227> Invalid Color Format",
                    description="Please use hex format, e.g., `#FFFFFF`.",
                    color=0xFF0000
                )
                error_embed.set_footer(text=f"Requested by {ctx.author}", icon_url=ctx.author.avatar.url)
                error_embed.timestamp = discord.utils.utcnow()
                await ctx.send(embed=error_embed, ephemeral=True)
                return

        await self.update_user_embeds(ctx.author.id, embed_name, **{property: value})

        embed = await self.retrieve_embed_data(ctx.author.id, embed_name)
        if embed:
            success_embed = discord.Embed(
                title="<a:fire:1235847103041900554> Embed Updated Successfully",
                description=f"Your embed **{embed_name}** has been updated. Here's the new preview:",
                color=0x2F3136
            )
            success_embed.set_footer(text=f"Requested by {ctx.author}", icon_url=ctx.author.avatar.url)
            success_embed.timestamp = discord.utils.utcnow()
            await ctx.send(embeds=[success_embed, embed])
        else:
            error_embed = discord.Embed(
                title="<:1001timeout:1233770920099844227> Update Failed",
                description="Failed to retrieve the updated embed.",
                color=0xFF0000
            )
            error_embed.set_footer(text=f"Requested by {ctx.author}", icon_url=ctx.author.avatar.url)
            error_embed.timestamp = discord.utils.utcnow()
            await ctx.send(embed=error_embed, ephemeral=True)

    async def role_autocomplete(self, interaction: discord.Interaction, current: str):
        roles = interaction.guild.roles
        filtered_roles = [discord.app_commands.Choice(name=role.name, value=str(role.id)) for role in roles if current.lower() in role.name.lower()]
        return filtered_roles

    @embed.command(name="button-add", description="Manually add a button to an embed")
    @app_commands.describe(
        embed_name="Name of the embed to attach the button",
        button_label="Label for the button, max 32 characters",
        button_style="Style of the button",
        link="URL for the button, required if style is Link",
        emoji="Emoji to display on the button, optional",
        role_to_give="ID of the role to give when the button is clicked, optional",
        send_embed="Name of the embed to send when the button is clicked, optional",
        custom_message="Custom message to send when the button is clicked, optional"
    )
    @app_commands.choices(button_style=[
        app_commands.Choice(name="Primary", value="Primary"),
        app_commands.Choice(name="Secondary", value="Secondary"),
        app_commands.Choice(name="Success", value="Success"),
        app_commands.Choice(name="Danger", value="Danger"),
        app_commands.Choice(name="Link", value="Link")
    ])
    @app_commands.autocomplete(role_to_give=role_autocomplete)
    async def add_button(
        self, interaction: discord.Interaction,
        embed_name: str, button_label: str, button_style: str,
        link: str = None, emoji: str = None, role_to_give: str = None,
        send_embed: str = None, custom_message: str = None
    ):
        user_id = str(interaction.user.id)
        custom_id = await self.add_button_info_db(
            user_id, embed_name, button_label, button_style, link, emoji, role_to_give, send_embed, custom_message
        )
        success_embed = discord.Embed(
            title="<a:fire:1235847103041900554> Button Added Successfully",
            description=f"Button added to embed '**{embed_name}**' with ID `{custom_id}`.",
            color=0x2F3136
        )
        success_embed.set_footer(text=f"Requested by {interaction.user}", icon_url=interaction.user.avatar.url)
        success_embed.timestamp = discord.utils.utcnow()
        await interaction.response.send_message(embed=success_embed, ephemeral=True)

    @embed.command(name="field-add", description="Manually add a field to an embed")
    @app_commands.describe(embed_name="Name of the embed", title="Title of the field", description="Description of the field", inline="Whether the field is inline")
    async def embed_add_field(self, interaction: discord.Interaction, embed_name: str, title: str, description: str = "", inline: bool = True):
        user_id = interaction.user.id
        async with aiosqlite.connect(self.db_path) as db:
            async with db.execute("SELECT MAX(field_id) FROM embed_fields WHERE user_id = ? AND embed_name = ?", (user_id, embed_name)) as cursor:
                result = await cursor.fetchone()
                new_field_id = (result[0] or 0) + 1

        await self.add_field_to_embed(user_id, embed_name, new_field_id, title, description, inline)
        success_embed = discord.Embed(
            title="<a:fire:1235847103041900554> Field Added Successfully",
            description=f"Field added to embed '**{embed_name}**'.",
            color=0x2F3136
        )
        success_embed.set_footer(text=f"Requested by {interaction.user}", icon_url=interaction.user.avatar.url)
        success_embed.timestamp = discord.utils.utcnow()
        await interaction.response.send_message(embed=success_embed, ephemeral=True)

    @embed.command(name="field-remove", description="Manually remove a field from an embed")
    @app_commands.describe(embed_name="Name of the embed", field_id="The position of the field to remove")
    async def remove_field(self, interaction: discord.Interaction, embed_name: str, field_id: int):
        user_id = interaction.user.id
        async with aiosqlite.connect(self.db_path) as db:
            async with db.execute("SELECT field_id FROM embed_fields WHERE user_id = ? AND embed_name = ? AND field_id = ?", (user_id, embed_name, field_id)) as cursor:
                field = await cursor.fetchone()
                if not field:
                    error_embed = discord.Embed(
                        title="<:1001timeout:1233770920099844227> Field Not Found",
                        description=f"No field found at position {field_id} in embed '**{embed_name}**'.",
                        color=0xFF0000
                    )
                    error_embed.set_footer(text=f"Requested by {interaction.user}", icon_url=interaction.user.avatar.url)
                    error_embed.timestamp = discord.utils.utcnow()
                    await interaction.response.send_message(embed=error_embed, ephemeral=True)
                    return

            await db.execute("DELETE FROM embed_fields WHERE user_id = ? AND embed_name = ? AND field_id = ?", (user_id, embed_name, field_id))
            await db.execute("""
                UPDATE embed_fields
                SET field_id = field_id - 1
                WHERE user_id = ? AND embed_name = ? AND field_id > ?
            """, (user_id, embed_name, field_id))
            await db.commit()

        success_embed = discord.Embed(
            title="<a:fire:1235847103041900554> Field Removed Successfully",
            description=f"Field {field_id} removed from embed '**{embed_name}**'.",
            color=0x2F3136
        )
        success_embed.set_footer(text=f"Requested by {interaction.user}", icon_url=interaction.user.avatar.url)
        success_embed.timestamp = discord.utils.utcnow()
        await interaction.response.send_message(embed=success_embed, ephemeral=True)


    @commands.hybrid_command(name="show", description="~(=^‥^)ノ Display a saved embed by name", aliases=["display", "s"])
    @app_commands.describe(embed_name="Name of the embed to display")
    async def show(self, ctx: commands.Context, embed_name: str):
        try:
            # Ensure to include the view when retrieving embed data
            embed_data = await self.retrieve_embed_data(ctx.author.id, embed_name, include_view=True)
            if embed_data:
                embed, view = embed_data  # Unpack both embed and view
                await ctx.send(embed=embed, view=view)  # Use the view that is either dynamically created or a default empty view
            else:
                await ctx.send("No embed found with that name.", ephemeral=True)
        except Exception as e:
            # logging.error(f"Error displaying embed {embed_name}: {str(e)}")
            await ctx.send("Failed to display the embed", ephemeral=True)
            print(f"{Fore.RED}Error displaying embed {embed_name}: {str(e)}")

    @embed.command(name="list", description="List your saved embeds")
    async def my_embeds(self, interaction: discord.Interaction):
        async with aiosqlite.connect(self.db_path) as db:
            async with db.execute("SELECT embed_name FROM user_embeds WHERE user_id = ?", (interaction.user.id,)) as cursor:
                embeds = await cursor.fetchall()

        if embeds:
            embed = discord.Embed(
                title="<a:83888settingsanimation:1233771395415015524> Your Embeds",
                description="Here's a list of your saved embeds:",
                color=0x2F3136
            )
            for i, embed_name in enumerate(embeds, 1):
                embed.add_field(name=f"Embed {i}", value=f"<:9177neonredarrowright:1240180166089769000> {embed_name[0]}", inline=False)
            embed.set_footer(text=f"Requested by {interaction.user}", icon_url=interaction.user.avatar.url)
            embed.timestamp = discord.utils.utcnow()
            await interaction.response.send_message(embed=embed)
        else:
            no_embeds = discord.Embed(
                title="<:8355moon:1233771385839681566> No Embeds Found",
                description="You haven't created any embeds yet.",
                color=0x2F3136
            )
            no_embeds.set_footer(text=f"Requested by {interaction.user}", icon_url=interaction.user.avatar.url)
            no_embeds.timestamp = discord.utils.utcnow()
            await interaction.response.send_message(embed=no_embeds, ephemeral=True)

    async def delete_embed(self, user_id: int, embed_name: str):
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute("DELETE FROM embed_fields WHERE user_id = ? AND embed_name = ?", (user_id, embed_name))
            await db.execute("DELETE FROM user_embeds WHERE user_id = ? AND embed_name = ?", (user_id, embed_name))
            await db.commit()

    @commands.hybrid_command(name="embed-delete", description="~(=^‥^)ノ Delete a specific embed by name", aliases=["del", "delete", "d", "remove"])
    async def delete_embed_command(self, ctx: commands.Context, embed_name: str):
        user_id = ctx.author.id
        embed = await self.retrieve_embed_data(user_id, embed_name)
        if not embed:
            error_embed = discord.Embed(
                title="<:1001timeout:1233770920099844227> Embed Not Found",
                description=f"No embed found with the name '**{embed_name}**'.",
                color=0x2F3136
            )
            error_embed.set_footer(text=f"Requested by {ctx.author}", icon_url=ctx.author.avatar.url)
            error_embed.timestamp = discord.utils.utcnow()
            await ctx.send(embed=error_embed, ephemeral=True)
            return

        await self.delete_embed(user_id, embed_name)
        success, message = await self.delete_buttons_for_embed_db(user_id, embed_name)

        if success:
            success_embed = discord.Embed(
                title="<a:fire:1235847103041900554> Embed Deleted",
                description=f"Embed '**{embed_name}**' and its buttons have been successfully deleted.",
                color=0x2F3136
            )
        else:
            if message == "No buttons found for this embed.":
                success_embed = discord.Embed(
                    title="<a:fire:1235847103041900554> Embed Deleted",
                    description=f"Embed '**{embed_name}**' has been successfully deleted. No buttons were associated with this embed.",
                    color=0x2F3136
                )
            else:
                success_embed = discord.Embed(
                    title="<a:fire:1235847103041900554> Embed Deleted (Partial)",
                    description=f"Embed '**{embed_name}**' has been deleted, but there was an issue with button deletion: {message}",
                    color=0x2F3136
                )

        success_embed.set_footer(text=f"Requested by {ctx.author}", icon_url=ctx.author.avatar.url)
        success_embed.timestamp = discord.utils.utcnow()
        await ctx.send(embed=success_embed, ephemeral=True)


    
            
async def setup(bot: commands.Bot):
    await bot.add_cog(EmbedProject(bot))


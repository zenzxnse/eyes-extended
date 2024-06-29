import discord
from discord.ext import commands
from discord import app_commands
import aiosqlite, aiohttp
import asyncio, json
import motor.motor_asyncio
import traceback, re
from urllib.parse import urlparse
from Extensions.Utility.roles import RoleMenuView  # Import the RoleMenuView class
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
        await interaction.response.send_message("Are you sure you want to delete this embed?", view=DeleteEmbedView(self.bot, self.user_id, self.embed_name), ephemeral=True)
    

        
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
        await interaction.response.send_modal(TitleModal(self.bot, self.user_id, self.embed_name, self.update_embed_message))

    @discord.ui.button(label="Edit Description", style=discord.ButtonStyle.gray)
    async def edit_description(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_modal(DescriptionModal(self.bot, self.user_id, self.embed_name, self.update_embed_message))
    @discord.ui.button(label="Edit Color", style=discord.ButtonStyle.gray)
    async def edit_color(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_modal(ColorModal(self.bot, self.user_id, self.embed_name, self.update_embed_message))

    @discord.ui.button(label="Edit Image", style=discord.ButtonStyle.gray)
    async def edit_image(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_modal(ImageModal(self.bot, self.user_id, self.embed_name, self.update_embed_message))
    @discord.ui.button(label="Edit Thumbnail", style=discord.ButtonStyle.gray)
    async def edit_thumbnail(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_modal(ThumbnailModal(self.bot, self.user_id, self.embed_name, self.update_embed_message))
    @discord.ui.button(label="Edit Footer", style=discord.ButtonStyle.gray)
    async def edit_footer(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_modal(FooterModal(self.bot, self.user_id, self.embed_name, self.update_embed_message))
    @discord.ui.button(label="Edit Author", style=discord.ButtonStyle.gray)
    async def edit_author(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_modal(AuthorModal(self.bot, self.user_id, self.embed_name, self.update_embed_message))
    @discord.ui.button(label="Add field", style=discord.ButtonStyle.gray)
    async def add_field(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_modal(AddFieldModal(self.bot, self.user_id, self.embed_name, self.update_embed_message))
    @discord.ui.button(label="Remove field", style=discord.ButtonStyle.gray)
    async def remove_field(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_modal(RemoveFieldModal(self.bot, self.user_id, self.embed_name, self.update_embed_message))

    @discord.ui.button(label="Edit Field", style=discord.ButtonStyle.gray)
    async def close_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_modal(EditFieldModal(self.bot, self.user_id, self.embed_name, self.update_embed_message))

class ButtonLookView(discord.ui.View):
    def __init__(self, bot, embed_name):
        super().__init__()
        self.bot = bot
        self.embed_name = embed_name  # Store the embed_name
        for style in ["Primary", "Secondary", "Success", "Danger"]:
            self.add_item(discord.ui.Button(label=style, style=getattr(discord.ButtonStyle, style.lower()), custom_id=style.lower()))

    async def interaction_check(self, interaction: discord.Interaction):
        selected_style = interaction.data['custom_id']
        await interaction.response.send_modal(ButtonModal(self.bot, selected_style, self.embed_name))

class ButtonModal(discord.ui.Modal, title="Please Enter The Button Details :"):
    def __init__(self, bot, style, embed_name):
        super().__init__()
        self.bot = bot
        self.style = style
        self.embed_name = embed_name  # Store the embed_name
        self.add_item(discord.ui.TextInput(label="Button Label", placeholder="Enter the button label or name...", style=discord.TextStyle.short, required=True))
        self.add_item(discord.ui.TextInput(label="Button Emoji", placeholder="Example: <:planet:1223294341204938872> or leave blank...", style=discord.TextStyle.short, required=False))

    async def on_submit(self, interaction: discord.Interaction):
        label = self.children[0].value
        emoji = self.children[1].value or None  # Handle empty emoji input correctly

        # Validate label length
        if len(label) > 32:
            await interaction.response.send_message("Button label must be 32 characters or fewer.", ephemeral=True)
            return

        # Validate emoji format if provided
        if emoji and not self.is_valid_emoji(emoji):
            await interaction.response.send_message("The provided emoji is invalid. Please enter a valid emoji or leave it blank.", ephemeral=True)
            return

        await interaction.response.send_message("What should this button do?", view=ButtonDropdownView(self.bot, label, emoji, self.style, self.embed_name), ephemeral=True)

    def is_valid_emoji(self, emoji):
        # Simple check to validate emoji format
        return emoji.startswith('<:') and emoji.endswith('>') and ':' in emoji

class ButtonDropdownView(discord.ui.View):
    def __init__(self, bot, label, emoji, style, embed_name):
        super().__init__()
        self.bot = bot
        self.label = label
        self.emoji = emoji
        self.style = style
        self.embed_name = embed_name  # Store the embed_name
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
            discord.SelectOption(label="Give Role", description="Assign a role"),
            discord.SelectOption(label="Send An Embedded Message", description="Send an embedded message"),
            discord.SelectOption(label="Send A Default Message", description="Send a plain message"),
            discord.SelectOption(label="Sends a role menu", description="the role menu which you have configured for ur server for self roles")
        ]

    async def callback(self, interaction: discord.Interaction):
        selected_option = self.values[0]
        if selected_option == "Give Role":
            await interaction.response.send_message("Select a role:", view=RoleDropdownView(self.bot, interaction.guild.roles, self.label, self.emoji, self.style, self.embed_name), ephemeral=True)
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
        guild_id = interaction.guild.id  # Get the guild ID from the interaction
        # Check if the role menu exists in the current guild
        role_menu_exists = await self.bot.get_cog("Roles").check_role_menu_exists(guild_id, role_menu_name)
        if role_menu_exists:
            additional_data = {'role_menu_name': role_menu_name, 'guild_id': guild_id}  # Include guild_id in additional_data
            await interaction.response.send_message("Role menu found! Finalizing button creation.", ephemeral=True)
            # Pass the correct label, emoji, and style to FinalizeButtonView
            await interaction.followup.send("Finalizing button creation.", view=FinalizeButtonView(self.bot, self.user_id, self.embed_name, self.label, self.emoji, self.style, "Sends a role menu", additional_data), ephemeral=True)
        else:
            await interaction.response.send_message("Role menu not found. Please try again.", ephemeral=True)

# Similar modifications should be made to other classes like RoleDropdownView, EmbedToButtons, etc.

class CustomMessageModal(discord.ui.Modal, title="Enter Custom Message"):
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
        await interaction.response.send_message("Finalizing button creation.", ephemeral=True)
        await interaction.followup.send(view=FinalizeButtonView(self.bot, interaction.user.id, self.embed_name, self.label, self.emoji, self.style, "Send A Default Message", additional_data), ephemeral=True)
class ButtomEmbedMessageView(discord.ui.View):
    def __init__(self, bot, user_id, embed_name):
        super().__init__()
        self.bot = bot
        self.user_id = user_id
        self.embed_name = embed_name

    @discord.ui.button(label="Embed Name", style=discord.ButtonStyle.gray)
    async def embed_name(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_modal(EmbedToButtons(self.bot, self.user_id, self.embed_name))

class EmbedToButtons(discord.ui.Modal, title="Embed Name"):
    def __init__(self, bot, user_id, original_embed_name, label, emoji, style):
        super().__init__()
        self.bot = bot
        self.user_id = user_id
        self.original_embed_name = original_embed_name  # This is the embed where the button is attached
        self.label = label
        self.emoji = emoji
        self.style = style
        self.send_embed_input = discord.ui.TextInput(
            label="Name Of Embed to Send",
            style=discord.TextStyle.short,
            placeholder="Enter the name of the embed to send...",
            required=True,
            default=original_embed_name  # Default to the original embed name, can be changed by user
        )
        self.add_item(self.send_embed_input)

    async def on_submit(self, interaction: discord.Interaction):
        send_embed_name = self.send_embed_input.value.strip()
        additional_data = {'send_embed': send_embed_name}
        await interaction.response.send_message(f"Embed to send updated to: {send_embed_name}", ephemeral=True)
        await interaction.followup.send("Finalizing button creation.", view=FinalizeButtonView(self.bot, self.user_id, self.original_embed_name, self.label, self.emoji, self.style, "Send An Embedded Message", additional_data), ephemeral=True)

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
        self.embed_name = embed_name  # Store the embed_name

        # Get the bot's highest role position in the guild
        bot_member = bot.get_guild(roles[0].guild.id).me  # Assuming all roles are from the same guild
        bot_highest_role_position = bot_member.top_role.position

        # Filter roles that the bot can manage
        manageable_roles = [
            role for role in roles
            if role.position < bot_highest_role_position and role.name != "@everyone"
        ]

        options = [
            discord.SelectOption(label=role.name, description=f"ID: {role.id}", value=str(role.id))
            for role in manageable_roles
        ]
        self.options = options

    async def callback(self, interaction: discord.Interaction):
        role_id = self.values[0]
        role = interaction.guild.get_role(int(role_id))  # Retrieve the role object using role_id
        if role:
            additional_data = {'role_to_give': role_id}
            await interaction.response.send_message(f"You selected: {role.name}", ephemeral=True)
            await interaction.followup.send("Finalizing button creation.", view=FinalizeButtonView(self.bot, interaction.user.id, self.embed_name, self.label, self.emoji, self.style, "Give Role", additional_data), ephemeral=True)
        else:
            await interaction.response.send_message("Role not found.", ephemeral=True)

class FinalizeButtonView(discord.ui.View):
    def __init__(self, bot, user_id, embed_name, label, emoji, style, functionality, additional_data):
        super().__init__()
        self.bot = bot
        self.user_id = user_id
        self.embed_name = embed_name  # This is the embed where the button is attached
        self.label = label
        self.emoji = emoji
        self.style = style
        self.functionality = functionality
        self.additional_data = additional_data

    @discord.ui.button(label="Confirm Button Creation", style=discord.ButtonStyle.green)
    async def confirm_button_creation(self, interaction: discord.Interaction, button: discord.ui.Button):
        embed_project = self.bot.get_cog("EmbedProject")
        if embed_project:
            # Ensure style is passed as a string
            style_name = self.style.name if isinstance(self.style, discord.ButtonStyle) else self.style
            custom_id = await embed_project.add_button_info_db(
                self.user_id, self.embed_name, self.label, style_name, None,
                self.emoji, self.additional_data.get('role_to_give'), self.additional_data.get('send_embed'), self.additional_data.get('custom_message'),
                guild_id=self.additional_data.get('guild_id'), role_menu_name=self.additional_data.get('role_menu_name')
            )
            await interaction.response.send_message(f"Button created successfully with ID {custom_id}!", ephemeral=True)
        else:
            await interaction.response.send_message("Failed to access EmbedProject cog. Button not created.", ephemeral=True)
           

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
        self.add_item(self.field_description)

    async def on_submit(self, interaction: discord.Interaction):
        field_title = self.field_title.value.strip()
        field_description = self.field_description.value.strip() if self.field_description.value else None

        # Add the new field to the embed
        try:
            await self.bot.get_cog("EmbedProject").add_field_to_embed(interaction.user.id, self.embed_name, field_title, field_description)
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
            required=False  # Allow users to submit an empty title
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
            required=True
        )
        self.add_item(self.new_description)

    async def on_submit(self, interaction: discord.Interaction):
        new_description = self.new_description.value.strip() if self.new_description.value else None
        if new_description == 'None':  # Check if the input is explicitly empty
            new_description = None  # Set to None to indicate removal of the description
        try:
            await self.bot.get_cog("EmbedProject").update_user_embeds(
                self.user_id, self.embed_name, description=self.new_description.value
            )
            embed = await self.bot.get_cog("EmbedProject").retrieve_embed_data(self.user_id, self.embed_name)
            if embed:
                await interaction.response.send_message(embed=embed, view=EmbedEditButtons(self.bot, self.user_id, self.embed_name), ephemeral=True)
            else:
                await interaction.response.send_message("Failed to update the description.", ephemeral=True)
        except Exception as e:
            await interaction.response.send_message('Oops! Something went wrong.', ephemeral=True)
            traceback.print_exception(type(e), e, e.__traceback__)

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
            required=True
        )
        self.add_item(self.new_color)

    async def on_submit(self, interaction: discord.Interaction):
        color_input = self.new_color.value.strip('#')
        try:
            # Validate the color format
            color_value = int(color_input, 16)
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
            required=True
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
            required=True
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

class FooterModal(discord.ui.Modal, title='Edit Footer'):
    def __init__(self, bot, user_id, embed_name, update_callback):
        super().__init__()
        self.bot = bot
        self.user_id = user_id
        self.embed_name = embed_name
        self.update_callback = update_callback

        # Footer text input (required)
        self.footer_text = discord.ui.TextInput(
            label='Footer Text',
            style=discord.TextStyle.short,
            placeholder='Enter footer text here...',
            required=True  # This field is required
        )
        self.add_item(self.footer_text)

        # Footer icon URL input (optional)
        self.footer_icon_url = discord.ui.TextInput(
            label='Footer Icon URL',
            style=discord.TextStyle.short,
            placeholder='Enter footer icon URL here... (optional)',
            required=False  # This field is optional
        )
        self.add_item(self.footer_icon_url)

    async def on_submit(self, interaction: discord.Interaction):
        footer_text = self.footer_text.value.strip()
        footer_icon_url = self.footer_icon_url.value.strip() if self.footer_icon_url.value else None

        # Check if the user explicitly wants to remove the footer text
        if footer_text.lower() == 'none':
            footer_text = None
            footer_icon_url = None  # Remove the icon URL as well since text is required for the icon

        # Validate the footer icon URL if provided and footer text is not None
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


class AuthorModal(discord.ui.Modal, title='Edit Author'):
    def __init__(self, bot, user_id, embed_name, update_callback):
        super().__init__()
        self.bot = bot
        self.user_id = user_id
        self.embed_name = embed_name
        self.update_callback = update_callback

        # Author text input (required)
        self.author_text = discord.ui.TextInput(
            label='Author Text',
            style=discord.TextStyle.short,
            placeholder='Enter author text here...',
            required=True  # This field is required
        )
        self.add_item(self.author_text)

        # Author icon URL input (optional)
        self.author_icon_url = discord.ui.TextInput(
            label='Author Icon URL',
            style=discord.TextStyle.short,
            placeholder='Enter author icon URL here... (optional)',
            required=False  # This field is optional
        )
        self.add_item(self.author_icon_url)

    async def on_submit(self, interaction: discord.Interaction):
        author_text = self.author_text.value.strip()
        author_icon_url = self.author_icon_url.value.strip() if self.author_icon_url.value else None

        # Validate the author icon URL if provided
        if author_icon_url and not is_valid_url(author_icon_url):
            await interaction.response.send_message("Invalid URL format for the author icon. Please enter a valid URL.", ephemeral=True)
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
                    return None

                columns = [description[0] for description in cursor.description]
                data = dict(zip(columns, row))

                embed = discord.Embed(title=data["title"], description=data["description"], color=data["color"])
                if data["footer_text"]:
                    embed.set_footer(text=data["footer_text"], icon_url=data["footer_icon_url"])
                if data["author_text"]:
                    embed.set_author(name=data["author_text"], icon_url=data["author_icon_url"])
                if data["thumbnail_url"]:
                    embed.set_thumbnail(url=data["thumbnail_url"])
                if data["image_url"]:
                    embed.set_image(url=data["image_url"])

                # Retrieve fields for the embed
                async with db.execute("SELECT title, description, inline FROM embed_fields WHERE user_id = ? AND embed_name = ? ORDER BY rowid", (user_id, embed_name)) as field_cursor:
                    fields = await field_cursor.fetchall()
                    for field in fields:
                        embed.add_field(name=field[0], value=field[1], inline=field[2])

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


    async def remove_field_from_embed(self, user_id: int, embed_name: str, field_position: int):
        async with aiosqlite.connect(self.db_path) as db:
            # Remove the field by rowid
            await db.execute("""
                DELETE FROM embed_fields 
                WHERE rowid = (SELECT rowid FROM embed_fields WHERE user_id = ? AND embed_name = ? ORDER BY rowid LIMIT 1 OFFSET ?)
            """, (user_id, embed_name, field_position - 1))
            await db.commit()

    async def add_field_to_embed(self, user_id: int, embed_name: str, title: str, description: str = "", inline: bool = True):
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute("INSERT INTO embed_fields (user_id, embed_name, title, description, inline) VALUES (?, ?, ?, ?, ?)", 
                            (user_id, embed_name, title, description, inline))
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
        
    async def update_field_in_embed(self, user_id, embed_name, field_position, new_title, new_text):
        async with aiosqlite.connect(self.db_path) as db:
            # Fetch the rowid for the field at the given position
            cursor = await db.execute("""
                SELECT rowid FROM embed_fields
                WHERE user_id = ? AND embed_name = ?
                ORDER BY rowid LIMIT 1 OFFSET ?
            """, (user_id, embed_name, field_position - 1))
            result = await cursor.fetchone()
            if not result:
                return False  # Field at the given position does not exist

            field_rowid = result[0]

            # Update the field using the rowid
            await db.execute("""
                UPDATE embed_fields
                SET title = ?, description = ?
                WHERE rowid = ?
            """, (new_title, new_text, field_rowid))
            await db.commit()
            return True
        
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
    
    @embed.command(name="builder", description="(✿◕‿◕) Either create or modify an existing embed.")
    @app_commands.describe(embed_name="Name of the embed to edit")
    async def embed_builder(self, interaction: discord.Interaction, embed_name: str):
        embed = await self.retrieve_embed_data(interaction.user.id, embed_name)
        if embed:
            view = EmbedbuilderButtons(self.bot, interaction.user.id, embed_name)
            await interaction.response.send_message(embed=embed, view=view, ephemeral=True)
        else:
            # Create a new embed with default values
            default_title = "New Embed"
            default_description = "This is a new embed. Edit it as you wish!"
            default_color = 0x000000  # Black color
            await self.save_user_embeds(
                interaction.user.id, embed_name,
                title=default_title, description=default_description, color=default_color
            )
            # Retrieve the newly created embed to display
            embed = await self.retrieve_embed_data(interaction.user.id, embed_name)
            if embed:
                view = EmbedbuilderButtons(self.bot, interaction.user.id, embed_name)
                await interaction.response.send_message("A new embed has been created.", embed=embed, view=view, ephemeral=True)
            else:
                await interaction.response.send_message("Failed to create a new embed.", ephemeral=True)
    
    @embed.command(name="through-webhook", description="*^____^* Send an embed through a webhook, in the specified channel.")
    @app_commands.describe(
        embed_name="Name of the embed to send",
        channel_mention="Mention the channel where the webhook will send the message"
    )
    async def send_through_webhook(self, interaction: discord.Interaction, embed_name: str, channel_mention: str):
        # Extract channel ID from mention
        try:
            channel_id = int(channel_mention.strip('<>#'))
        except ValueError:
            await interaction.response.send_message("Invalid channel mention.", ephemeral=True)
            return

        # Retrieve the channel from the channel ID
        channel = self.bot.get_channel(channel_id)
        if not channel:
            await interaction.response.send_message("Invalid channel ID provided.", ephemeral=True)
            return

        # Check if the bot has permissions to manage webhooks in the channel
        if not channel.permissions_for(interaction.guild.me).manage_webhooks:
            await interaction.response.send_message("I do not have permission to manage webhooks in this channel.", ephemeral=True)
            return

        # Retrieve the embed data
        embed_data = await self.retrieve_embed_data(interaction.user.id, embed_name, include_view=True)
        if not embed_data:
            await interaction.response.send_message(f"No embed found with the name '{embed_name}'.", ephemeral=True)
            return

        embed, view = embed_data

        # Find an existing webhook created by the bot
        webhooks = await channel.webhooks()
        webhook = next((wh for wh in webhooks if wh.user == self.bot.user), None)

        # If no existing webhook found, create a new one
        if not webhook:
            webhook = await channel.create_webhook(name="Bot Webhook")

        # Send the message through the webhook
        try:
            await webhook.send(embed=embed, view=view)
            await interaction.response.send_message("Message sent successfully through the webhook., You can modify this webhook in the channel settings\n\n```yml\nEdit Channel > Integrations > Webhooks\n```", ephemeral=True)
        except Exception as e:
            await interaction.response.send_message(f"An error occurred: {str(e)}", ephemeral=True)

    async def fetch_user_buttons(self, user_id):
        async with aiosqlite.connect('db/buttons.db') as db:
            async with db.execute("SELECT label, custom_id, embed_name FROM buttons WHERE user_id = ?", (user_id,)) as cursor:
                buttons = await cursor.fetchall()
                if not buttons:
                    return None, "No buttons found for the user."
            user_buttons = [f"1. {button[0]}\n> **__ID: {button[1]}__**, embed = {button[2]}" for button in buttons]
            return user_buttons, None

    @embed.command(name="buttons", description="(✿◡‿◡) View your embed buttons.")
    async def my_buttons(self, interaction: discord.Interaction):
        user_id = interaction.user.id  # Keep as integer
        user_buttons, error_message = await self.fetch_user_buttons(user_id)

        if error_message:
            await interaction.response.send_message(error_message, ephemeral=True)
            return

        if user_buttons:
            # Generate a numbered list of buttons
            description = "\n\n".join(f"{index + 1}. {button}" for index, button in enumerate(user_buttons))
            embed = discord.Embed(title="Your Buttons", description=description, color=0x8B0000)
            await interaction.response.send_message(embed=embed, ephemeral=True)
        else:
            await interaction.response.send_message("You have not created any buttons.", ephemeral=True)

    @embed.command(name="delete-button", description="^_^ Delete a button from an embed.")
    @app_commands.describe(custom_id="The custom ID of the button to delete")
    async def delete_button(self, interaction: discord.Interaction, custom_id: str):
        user_id = interaction.user.id
        success, message = await self.delete_button_info_db(user_id, custom_id)
        if not success:
            if "not found" in message:
                message = f"No button found with ID: {custom_id}. Please check the ID and try again."
            elif "do not own" in message:
                message = "You do not have permission to delete this button."
        await interaction.response.send_message(message, ephemeral=True)

    quick = discord.app_commands.Group(name="quick", description="Quickly create an embed.")
    @quick.command(name="embed", description=";) Quickly create an embed!")
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
            await interaction.response.send_message("Invalid color format. Please use hex format, e.g., #FFFFFF.", ephemeral=True)
            return

        # Validate URLs
        def validate_url(url):
            if url and not (url.startswith("http://") or url.startswith("https://")):
                return False
            return True

        invalid_urls = []
        if footer_icon_url and not validate_url(footer_icon_url):
            invalid_urls.append("footer icon URL")
        if author_icon_url and not validate_url(author_icon_url):
            invalid_urls.append("author icon URL")
        if thumbnail_url and not validate_url(thumbnail_url):
            invalid_urls.append("thumbnail URL")
        if image_url and not validate_url(image_url):
            invalid_urls.append("image URL")

        if invalid_urls:
            await interaction.response.send_message(f"Invalid URL provided for {', '.join(invalid_urls)}. URLs must start with http:// or https://", ephemeral=True)
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
            await interaction.response.send_message(embed=embed, ephemeral=True)
        else:
            await interaction.response.send_message("Failed to create or retrieve the embed.", ephemeral=True)

    @commands.hybrid_command(name="embed-edit", description="(ﾉ◕ヮ◕)ﾉ*:Edit a specific property of an existing embed :D try ;embed edit embname title hello world")
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
    async def edit_embed(self, ctx: commands.Context, embed_name: str, property: str, *,value: str):
        if value.lower() == 'none':
            value = None

        if property in ["footer_icon_url", "author_icon_url", "thumbnail_url", "image_url"] and value:
            if not (value.startswith("http://") or value.startswith("https://")):
                await ctx.send(f"Invalid URL provided for {property}. URLs must start with http:// or https://", ephemeral=True)
                return

        if property == "color" and value:
            try:
                value = int(value.strip("#"), 16)
            except ValueError:
                await ctx.send("Invalid color format. Please use hex format, e.g., #FFFFFF.", ephemeral=True)
                return

        await self.update_user_embeds(ctx.author.id, embed_name, **{property: value})

        embed = await self.retrieve_embed_data(ctx.author.id, embed_name)
        if embed:
            await ctx.send(f"Embed '{embed_name}' updated successfully.", embed=embed)
        else:
            await ctx.send("Failed to retrieve the updated embed.", ephemeral=True)

    async def role_autocomplete(self, interaction: discord.Interaction, current: str):
    # Fetch all roles from the guild
        roles = interaction.guild.roles
        # Filter roles based on the current user input and create choices
        filtered_roles = [discord.app_commands.Choice(name=role.name, value=str(role.id)) for role in roles if current.lower() in role.name.lower()]
        # Return the filtered list of choices
        return filtered_roles
    @embed.command(name="button-add", description="(￣﹏￣；) Manually add a button to an embed. but why?, just use /embed builder")
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
        user_id = str(interaction.user.id)  # Ensure user_id is a string
        custom_id = await self.add_button_info_db(
            user_id, embed_name, button_label, button_style, link, emoji, role_to_give, send_embed, custom_message
        )
        await interaction.response.send_message(f"Button added to embed '{embed_name}' with ID {custom_id}.", ephemeral=True)

    @embed.command(name="field-add", description="(￣﹏￣；) Manually add a field to an embed, but why?, just use /embed builder")
    @app_commands.describe(embed_name="Name of the embed", title="Title of the field", description="Description of the field", inline="Whether the field is inline")
    async def embed_add_field(self, interaction: discord.Interaction, embed_name: str, title: str, description: str = "", inline: bool = True):
        user_id = interaction.user.id
        # Retrieve current fields to determine the new field_id
        async with aiosqlite.connect(self.db_path) as db:
            async with db.execute("SELECT MAX(field_id) FROM embed_fields WHERE user_id = ? AND embed_name = ?", (user_id, embed_name)) as cursor:
                result = await cursor.fetchone()
                new_field_id = (result[0] or 0) + 1  # Increment the highest field_id

        # Add the new field
        await self.add_field_to_embed(user_id, embed_name, new_field_id, title, description, inline)
        await interaction.response.send_message(f"Field added to embed '{embed_name}'.", ephemeral=True)
    @embed.command(name="field-remove", description="(￣﹏￣；) Manually remove a field from an embed, but why?, just use /embed builder")
    @app_commands.describe(embed_name="Name of the embed", field_id="The position of the field to remove")
    async def remove_field(self, interaction: discord.Interaction, embed_name: str, field_id: int):
        user_id = interaction.user.id
        async with aiosqlite.connect(self.db_path) as db:
            # Check if the field exists before attempting to remove it
            async with db.execute("SELECT field_id FROM embed_fields WHERE user_id = ? AND embed_name = ? AND field_id = ?", (user_id, embed_name, field_id)) as cursor:
                field = await cursor.fetchone()
                if not field:
                    await interaction.response.send_message(f"No field found at position {field_id} in embed '{embed_name}'.", ephemeral=True)
                    return

            # Proceed to remove the field
            await db.execute("DELETE FROM embed_fields WHERE user_id = ? AND embed_name = ? AND field_id = ?", (user_id, embed_name, field_id))
            await db.commit()

            # Reorder the remaining fields
            await db.execute("""
                UPDATE embed_fields
                SET field_id = field_id - 1
                WHERE user_id = ? AND embed_name = ? AND field_id > ?
            """, (user_id, embed_name, field_id))
            await db.commit()

        await interaction.response.send_message(f"Field {field_id} removed from embed '{embed_name}'.", ephemeral=True)

    @embed.command(name="field-edit", description="(￣﹏￣；) Oudated use embed builder, unsure if this works or not.")
    @app_commands.describe(embed_name="Name of the embed", field_id="ID of the field to edit", title="New title of the field", description="New description of the field")
    async def embed_edit_field(self, interaction: discord.Interaction, embed_name: str, field_id: int, title: str, description: str = None):
        user_id = interaction.user.id
        # Update the field
        async with aiosqlite.connect(self.db_path) as db:
            update_clause = "title = ?"
            params = [title, user_id, embed_name, field_id]
            if description is not None:
                update_clause += ", description = ?"
                params.insert(1, description)

            await db.execute(f"UPDATE embed_fields SET {update_clause} WHERE user_id = ? AND embed_name = ? AND field_id = ?", params)
            await db.commit()

        await interaction.response.send_message(f"Field {field_id} in embed '{embed_name}' updated.", ephemeral=True)

    @commands.hybrid_command(name="show", description="~(=^‥^)ノ Display a saved embed by name e.g ;s embedname", aliases=["display", "s"])
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
            await ctx.send("Failed to display the embed.", ephemeral=True)

    @embed.command(name="list", description="List your saved embeds")
    async def my_embeds(self, interaction: discord.Interaction):
        async with aiosqlite.connect(self.db_path) as db:
            async with db.execute("SELECT embed_name FROM user_embeds WHERE user_id = ?", (interaction.user.id,)) as cursor:
                embeds = await cursor.fetchall()

        if embeds:
            embed = discord.Embed(title="Your Embeds", color=0x8B0000)  # Dark red color
            for embed_name in embeds:
                embed.add_field(name="Embed Name", value=embed_name[0], inline=True)

            await interaction.response.send_message(embed=embed)
        else:
            await interaction.response.send_message("You have not created any embeds.", ephemeral=True)

    async def delete_embed(self, user_id: int, embed_name: str):
        async with aiosqlite.connect(self.db_path) as db:
            # Delete fields associated with the embed first
            await db.execute("DELETE FROM embed_fields WHERE user_id = ? AND embed_name = ?", (user_id, embed_name))
            # Then delete the embed itself
            await db.execute("DELETE FROM user_embeds WHERE user_id = ? AND embed_name = ?", (user_id, embed_name))
            await db.commit()

    @commands.hybrid_command(name="embed-delete", description="~(=^‥^)ノ ;del embedname, delete a specific embed by name or open it in embed builder!", aliases=["del", "delete", "d", "remove"])
    async def delete_embed_command(self, ctx: commands.Context, embed_name: str):
        user_id = ctx.author.id  # Get the user ID from the context

        # Check if the embed exists before attempting to delete
        embed = await self.retrieve_embed_data(user_id, embed_name)
        if not embed:
            await ctx.send(f"No embed found with the name '{embed_name}'.", ephemeral=True)
            return

        # Proceed with deletion of the embed
        await self.delete_embed(user_id, embed_name)

        # Attempt to delete associated buttons from buttons.json
        success, message = await self.delete_buttons_for_embed_db(user_id, embed_name)
        if not success:
            if message == "No buttons found for this embed.":
                # If no buttons were found, confirm deletion of the embed only
                await ctx.send(f"Embed '{embed_name}' has been successfully deleted. No buttons were associated with this embed.", ephemeral=True)
            else:
                # If there was a genuine failure in deleting buttons, report it
                await ctx.send(f"Failed to delete buttons for '{embed_name}': {message}", ephemeral=True)
        else:
            # If buttons were successfully deleted, confirm deletion of both
            await ctx.send(f"Embed '{embed_name}' and its buttons have been successfully deleted.", ephemeral=True)


    
            
async def setup(bot: commands.Bot):
    await bot.add_cog(EmbedProject(bot))


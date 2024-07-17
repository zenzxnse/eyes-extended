import discord
import os
import aiosqlite
import urllib.parse
from discord.ext import commands
from discord import app_commands



"""
Welcome System for Discord Bot

This module implements a comprehensive welcome system for a Discord bot. It provides functionality to:
1. Enable/disable welcome messages for new members
2. Customize welcome messages and embeds
3. Set up and manage welcome channels
4. Store and retrieve welcome configurations using SQLite database

Key Features:
- Database setup and management for storing welcome configurations
- Commands to enable/disable welcome messages
- Commands to customize welcome embed properties (title, description, color, footer, etc.)
- Commands to set welcome message text
- Event listener for new member joins to send customized welcome messages

Usage:
1. Add this cog to your bot
2. Use the provided commands to set up and customize your welcome system
3. The bot will automatically send welcome messages to new members based on your configuration

Note: This module requires the 'discord.py' library and 'aiosqlite' for database operations.
"""



DB_PATH = "db/welcome.db"

async def db_setup():
    """
    Set up the SQLite database for storing welcome configurations.
    
    This function creates two tables:
    1. 'welcome' table for storing general welcome settings
    2. 'welcome_embed' table for storing embed-specific settings
    """
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("""CREATE TABLE IF NOT EXISTS welcome 
                         (guild_id INTEGER PRIMARY KEY,
                         welcome_enabled BOOLEAN DEFAULT FALSE, 
                         welcome_message TEXT DEFAULT 'Welcome to the server, {user_mention}!',
                         welcome_channel INTEGER,
                         welcome_role INTEGER)""")
        await db.execute("""CREATE TABLE IF NOT EXISTS welcome_embed
                         (guild_id INTEGER PRIMARY KEY,
                         title TEXT DEFAULT 'Welcome to {guild.name}!',
                         description TEXT DEFAULT 'We hope you enjoy your stay!',
                         color TEXT DEFAULT '#00ff00',
                         footer_text TEXT,
                         footer_icon_url TEXT,
                         author_name TEXT,
                         author_icon_url TEXT,
                         image_url TEXT,
                         thumbnail_url TEXT,
                         timestamp BOOLEAN DEFAULT TRUE)""")
        await db.commit()

async def get_welcome_data(guild_id: int):
    """
    Retrieve welcome configuration data for a specific guild.

    Args:
        guild_id (int): The ID of the guild to fetch data for.

    Returns:
        dict: A dictionary containing the welcome configuration for the guild.
    """
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute("SELECT * FROM welcome WHERE guild_id = ?", (guild_id,)) as cursor:
            return await cursor.fetchone()

async def get_welcome_embed_data(guild_id: int):
    """
    Retrieve welcome embed configuration data for a specific guild.

    Args:
        guild_id (int): The ID of the guild to fetch embed data for.

    Returns:
        dict: A dictionary containing the welcome embed configuration for the guild.
    """
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute("SELECT * FROM welcome_embed WHERE guild_id = ?", (guild_id,)) as cursor:
            return await cursor.fetchone()

class Welcome(commands.Cog):
    """
    A cog that implements a welcome system for new members joining a Discord server.
    """

    def __init__(self, bot: commands.Bot):
        self.bot = bot

    welcome = app_commands.Group(name="welcome", description="Welcome system commands")

    @welcome.command(name="enable", description="Enable welcome messages")
    @app_commands.describe(welcome_channel="The channel to send welcome messages in")
    async def welcome_enable(self, interaction: discord.Interaction, welcome_channel: discord.TextChannel):
        """
        Enable welcome messages for the guild and set the welcome channel.

        Args:
            interaction (discord.Interaction): The interaction object.
            welcome_channel (discord.TextChannel): The channel where welcome messages will be sent.
        """
        async with aiosqlite.connect(DB_PATH) as db:
            await db.execute("INSERT OR REPLACE INTO welcome (guild_id, welcome_enabled, welcome_channel) VALUES (?, TRUE, ?)",
                             (interaction.guild_id, welcome_channel.id))
            await db.commit()
        await interaction.response.send_message(f"Welcome messages enabled in {welcome_channel.mention}.")

    @welcome.command(name="disable", description="Disable welcome messages")
    async def welcome_disable(self, interaction: discord.Interaction):
        """
        Disable welcome messages for the guild.

        Args:
            interaction (discord.Interaction): The interaction object.
        """
        async with aiosqlite.connect(DB_PATH) as db:
            await db.execute("UPDATE welcome SET welcome_enabled = FALSE WHERE guild_id = ?", (interaction.guild_id,))
            await db.commit()
        await interaction.response.send_message("Welcome messages disabled.")

    @welcome.command(name="embed-edit", description="Edit welcome embed properties")
    @app_commands.describe(
        title="Embed title",
        description="Embed description",
        color="Embed color (hex format)",
        footer_text="Footer text",
        footer_icon_url="Footer icon URL",
        author_name="Author name",
        author_icon_url="Author icon URL"
    )
    async def welcome_embed_edit(self, interaction: discord.Interaction, title: str = None, description: str = None,
                                 color: str = None, footer_text: str = None, footer_icon_url: str = None,
                                 author_name: str = None, author_icon_url: str = None):
        """
        Edit the properties of the welcome embed.

        Args:
            interaction (discord.Interaction): The interaction object.
            title (str, optional): The title of the embed.
            description (str, optional): The description of the embed.
            color (str, optional): The color of the embed in hex format.
            footer_text (str, optional): The text to display in the footer.
            footer_icon_url (str, optional): The URL of the footer icon.
            author_name (str, optional): The name to display in the author field.
            author_icon_url (str, optional): The URL of the author icon.
        """
        async with aiosqlite.connect(DB_PATH) as db:
            updates = []
            values = []
            if title is not None:
                updates.append("title = ?")
                values.append(title)
            if description is not None:
                updates.append("description = ?")
                values.append(description)
            if color is not None:
                if not color.startswith('#'):
                    color = f'#{color}'
                updates.append("color = ?")
                values.append(color)
            if footer_text is not None:
                updates.append("footer_text = ?")
                values.append(footer_text)
            if footer_icon_url is not None:
                updates.append("footer_icon_url = ?")
                values.append(footer_icon_url)
            if author_name is not None:
                updates.append("author_name = ?")
                values.append(author_name)
            if author_icon_url is not None:
                updates.append("author_icon_url = ?")
                values.append(author_icon_url)
            
            if updates:
                query = f"INSERT OR REPLACE INTO welcome_embed (guild_id, {', '.join(updates)}) VALUES (?, {', '.join(['?'] * len(updates))})"
                values.insert(0, interaction.guild_id)
                await db.execute(query, values)
                await db.commit()
                await interaction.response.send_message("Welcome embed updated successfully.")
            else:
                await interaction.response.send_message("No changes were made to the welcome embed.")

    @welcome.command(name="embed-image", description="Set the welcome embed image")
    @app_commands.describe(url="Image URL", attachment="Uploaded image")
    async def welcome_embed_image(self, interaction: discord.Interaction, url: str = None, attachment: discord.Attachment = None):
        """
        Set the image for the welcome embed.

        Args:
            interaction (discord.Interaction): The interaction object.
            url (str, optional): The URL of the image to use.
            attachment (discord.Attachment, optional): An uploaded image attachment.
        """
        if url is None and attachment is None:
            return await interaction.response.send_message("Please provide either a URL or an image attachment.")
        
        image_url = url or attachment.url
        if not self.is_valid_url(image_url):
            return await interaction.response.send_message("Invalid URL provided.")
        
        async with aiosqlite.connect(DB_PATH) as db:
            await db.execute("INSERT OR REPLACE INTO welcome_embed (guild_id, image_url) VALUES (?, ?)",
                             (interaction.guild_id, image_url))
            await db.commit()
        await interaction.response.send_message("Welcome embed image updated successfully.")

    @welcome.command(name="embed-thumbnail", description="Set the welcome embed thumbnail")
    @app_commands.describe(url="Thumbnail URL", attachment="Uploaded thumbnail image")
    async def welcome_embed_thumbnail(self, interaction: discord.Interaction, url: str = None, attachment: discord.Attachment = None):
        """
        Set the thumbnail for the welcome embed.

        Args:
            interaction (discord.Interaction): The interaction object.
            url (str, optional): The URL of the thumbnail image to use.
            attachment (discord.Attachment, optional): An uploaded thumbnail image attachment.
        """
        if url is None and attachment is None:
            return await interaction.response.send_message("Please provide either a URL or an image attachment.")
        
        thumbnail_url = url or attachment.url
        if not self.is_valid_url(thumbnail_url):
            return await interaction.response.send_message("Invalid URL provided.")
        
        async with aiosqlite.connect(DB_PATH) as db:
            await db.execute("INSERT OR REPLACE INTO welcome_embed (guild_id, thumbnail_url) VALUES (?, ?)",
                             (interaction.guild_id, thumbnail_url))
            await db.commit()
        await interaction.response.send_message("Welcome embed thumbnail updated successfully.")

    @welcome.command(name="message-set", description="Set the welcome message")
    @app_commands.describe(message="The welcome message to be sent. You can use placeholders like {user_mention}, {user_name}, {user_display_name}, {member_count}, and {guild.name}.")
    async def welcome_message_set(self, interaction: discord.Interaction, *, message: str):
        """
        Set the welcome message text.

        Args:
            interaction (discord.Interaction): The interaction object.
            message (str): The welcome message text, which can include placeholders.
        """
        async with aiosqlite.connect(DB_PATH) as db:
            await db.execute("UPDATE welcome SET welcome_message = ? WHERE guild_id = ?",
                             (message, interaction.guild_id))
            await db.commit()
        await interaction.response.send_message("Welcome message updated successfully.")

    @welcome.command(name="embed-remove", description="Remove a property from the welcome embed")
    @app_commands.describe(property="The property to remove")
    @app_commands.choices(property=[
        app_commands.Choice(name="Title", value="title"),
        app_commands.Choice(name="Description", value="description"),
        app_commands.Choice(name="Color", value="color"),
        app_commands.Choice(name="Footer Text", value="footer_text"),
        app_commands.Choice(name="Footer Icon", value="footer_icon_url"),
        app_commands.Choice(name="Author Name", value="author_name"),
        app_commands.Choice(name="Author Icon", value="author_icon_url"),
        app_commands.Choice(name="Image", value="image_url"),
        app_commands.Choice(name="Thumbnail", value="thumbnail_url"),
    ])
    async def welcome_embed_remove(self, interaction: discord.Interaction, property: str):
        """
        Remove a specific property from the welcome embed.

        Args:
            interaction (discord.Interaction): The interaction object.
            property (str): The name of the property to remove.
        """
        async with aiosqlite.connect(DB_PATH) as db:
            await db.execute(f"UPDATE welcome_embed SET {property} = NULL WHERE guild_id = ?", (interaction.guild_id,))
            await db.commit()
        await interaction.response.send_message(f"Removed {property} from the welcome embed.")

    @staticmethod
    def is_valid_url(url: str) -> bool:
        """
        Check if a given URL is valid.

        Args:
            url (str): The URL to validate.

        Returns:
            bool: True if the URL is valid, False otherwise.
        """
        try:
            result = urllib.parse.urlparse(url)
            return all([result.scheme, result.netloc])
        except ValueError:
            return False

    @commands.Cog.listener()
    async def on_member_join(self, member: discord.Member):
        """
        Event listener for when a new member joins the server.
        Sends a welcome message and embed if enabled.

        Args:
            member (discord.Member): The member who joined the server.
        """
        welcome_data = await get_welcome_data(member.guild.id)
        if not welcome_data or not welcome_data['welcome_enabled']:
            return

        channel = self.bot.get_channel(welcome_data['welcome_channel'])
        if not channel:
            return

        embed_data = await get_welcome_embed_data(member.guild.id)
        embed = discord.Embed()
        if embed_data:
            if embed_data['title']:
                embed.title = self.format_string(embed_data['title'], member)
            
            # Ensure there's always a description
            embed.description = self.format_string(embed_data['description'], member) if embed_data['description'] else f"Welcome to {member.guild.name}!"
            
            if embed_data['color']:
                embed.color = discord.Color.from_str(embed_data['color'])
            if embed_data['footer_text']:
                embed.set_footer(text=self.format_string(embed_data['footer_text'], member), icon_url=embed_data['footer_icon_url'])
            if embed_data['author_name']:
                embed.set_author(name=self.format_string(embed_data['author_name'], member), icon_url=embed_data['author_icon_url'])
            if embed_data['image_url']:
                embed.set_image(url=embed_data['image_url'])
            if embed_data['thumbnail_url']:
                embed.set_thumbnail(url=embed_data['thumbnail_url'])
            if embed_data['timestamp']:
                embed.timestamp = discord.utils.utcnow()
        else:
            # If no embed data is found, create a default embed
            embed.title = f"Welcome to {member.guild.name}!"
            embed.description = f"Welcome, {member.mention}! You are our {self.get_ordinal(member.guild.member_count)} member."

        welcome_message = self.format_string(welcome_data['welcome_message'], member)
        
        try:
            await channel.send(content=welcome_message, embed=embed)
        except discord.HTTPException as e:
            print(f"Error sending welcome message: {e}")

    def format_string(self, string: str, member: discord.Member) -> str:
        """
        Format a string with member and guild information.

        Args:
            string (str): The string to format.
            member (discord.Member): The member object to use for formatting.

        Returns:
            str: The formatted string.
        """
        return string.format(
            user=member,
            guild=member.guild,
            user_mention=member.mention,
            user_name=member.name,
            user_display_name=member.display_name,
            member_count=self.get_ordinal(member.guild.member_count)
        )

    @staticmethod
    def get_ordinal(n: int) -> str:
        suffix = ['th', 'st', 'nd', 'rd', 'th'][min(n % 10, 4)]
        if 11 <= (n % 100) <= 13:
            suffix = 'th'
        return f"{n}{suffix}"

async def setup(bot: commands.Bot):
    await bot.add_cog(Welcome(bot))
    await db_setup()
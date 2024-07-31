import discord
import os, datetime
import aiosqlite
import urllib.parse
from discord.ext import commands
from discord import app_commands

def parse_color(color_str):
    if color_str is None:
        return None
    if isinstance(color_str, int):
        return discord.Color(color_str)
    if color_str.startswith('#'):
        return discord.Color.from_str(color_str)
    try:
        return discord.Color(int(color_str))
    except ValueError:
        return None

"""
Goodbye System for Discord Bot

This module implements a comprehensive goodbye system for a Discord bot. It provides functionality to:
1. Enable/disable goodbye messages for members leaving
2. Customize goodbye messages and embeds
3. Set up and manage goodbye channels
4. Store and retrieve goodbye configurations using SQLite database

Key Features:
- Database setup and management for storing goodbye configurations
- Commands to enable/disable goodbye messages
- Commands to customize goodbye embed properties (title, description, color, footer, etc.)
- Commands to set goodbye message text
- Event listener for member removals to send customized goodbye messages

Usage:
1. Add this cog to your bot
2. Use the provided commands to set up and customize your goodbye system
3. The bot will automatically send goodbye messages when members leave based on your configuration

Note: This module requires the 'discord.py' library and 'aiosqlite' for database operations.
"""

DB_PATH = "db/goodbye.db"

async def db_setup():
    """
    Set up the SQLite database for storing goodbye configurations.
    
    This function creates two tables:
    1. 'goodbye' table for storing general goodbye settings
    2. 'goodbye_embed' table for storing embed-specific settings
    """
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("""CREATE TABLE IF NOT EXISTS goodbye 
                         (guild_id INTEGER PRIMARY KEY,
                         goodbye_enabled BOOLEAN DEFAULT FALSE, 
                         goodbye_message TEXT DEFAULT "Goodbye, {user_name}. We'll miss you!",
                         goodbye_channel INTEGER)""")
        await db.execute("""CREATE TABLE IF NOT EXISTS goodbye_embed
                         (guild_id INTEGER PRIMARY KEY,
                         title TEXT DEFAULT "Farewell, {user_name}!",
                         description TEXT DEFAULT "We hope to see you again soon!",
                         color TEXT DEFAULT "#ff0000",
                         footer_text TEXT,
                         footer_icon_url TEXT,
                         author_name TEXT,
                         author_icon_url TEXT,
                         image_url TEXT,
                         thumbnail_url TEXT,
                         timestamp BOOLEAN DEFAULT TRUE)""")
        await db.commit()

async def get_goodbye_data(guild_id: int):
    """
    Retrieve goodbye configuration data for a specific guild.

    Args:
        guild_id (int): The ID of the guild to fetch data for.

    Returns:
        dict: A dictionary containing the goodbye configuration for the guild.
    """
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute("SELECT * FROM goodbye WHERE guild_id = ?", (guild_id,)) as cursor:
            return await cursor.fetchone()

async def get_goodbye_embed_data(guild_id: int):
    """
    Retrieve goodbye embed data for a specific guild.

    Args:
        guild_id (int): The ID of the guild to fetch embed data for.

    Returns:
        dict: A dictionary containing the goodbye embed data for the guild.
    """
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute("SELECT * FROM goodbye_embed WHERE guild_id = ?", (guild_id,)) as cursor:
            return await cursor.fetchone()

class Goodbye(commands.Cog):
    """
    A cog that implements a goodbye system for members leaving a Discord server.
    """

    def __init__(self, bot: commands.Bot):
        self.bot = bot

    goodbye = app_commands.Group(name="goodbye", description="Goodbye system commands")

    @goodbye.command(name="enable", description="Enable goodbye messages")
    @app_commands.describe(goodbye_channel="The channel to send goodbye messages in")
    async def goodbye_enable(self, interaction: discord.Interaction, goodbye_channel: discord.TextChannel):
        """
        Enable goodbye messages for the server.

        Args:
            interaction (discord.Interaction): The interaction object.
            goodbye_channel (discord.TextChannel): The channel to send goodbye messages in.
        """
        # Check if the interaction is None (called programmatically)
        if interaction is None:
            guild_id = goodbye_channel.guild.id
        else:
            guild_id = interaction.guild_id

        async with aiosqlite.connect(DB_PATH) as db:
            await db.execute("""INSERT OR REPLACE INTO goodbye 
                             (guild_id, goodbye_enabled, goodbye_channel) 
                             VALUES (?, TRUE, ?)""", 
                             (guild_id, goodbye_channel.id))
            await db.commit()
        
        if interaction:
            await interaction.response.send_message(f"Goodbye messages enabled in {goodbye_channel.mention}.")
        print(f"Goodbye system enabled for guild ID: {guild_id}, channel ID: {goodbye_channel.id}")

    @goodbye.command(name="disable", description="Disable goodbye messages")
    async def goodbye_disable(self, interaction: discord.Interaction):
        """
        Disable goodbye messages for the guild.

        Args:
            interaction (discord.Interaction): The interaction object.
        """
        async with aiosqlite.connect(DB_PATH) as db:
            await db.execute("UPDATE goodbye SET goodbye_enabled = FALSE WHERE guild_id = ?", (interaction.guild_id,))
            await db.commit()
        await interaction.response.send_message("Goodbye messages disabled.")

    @goodbye.command(name="embed-edit", description="Edit goodbye embed properties")
    @app_commands.describe(
        title="Embed title",
        description="Embed description",
        color="Embed color (hex format or integer)",
        footer_text="Footer text",
        footer_icon_url="Footer icon URL",
        author_name="Author name",
        author_icon_url="Author icon URL"
    )
    async def goodbye_embed_edit(self, interaction: discord.Interaction, title: str = None, description: str = None,
                                 color: str = None, footer_text: str = None, footer_icon_url: str = None,
                                 author_name: str = None, author_icon_url: str = None):
        """
        Edit the properties of the goodbye embed.

        Args:
            interaction (discord.Interaction): The interaction object.
            title (str, optional): The title of the embed.
            description (str, optional): The description of the embed.
            color (str, optional): The color of the embed in hex format or as an integer.
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
                parsed_color = parse_color(color)
                if parsed_color:
                    updates.append("color = ?")
                    values.append(str(parsed_color.value))
                else:
                    return await interaction.response.send_message("Invalid color format. Please use hex (e.g., #FF0000) or integer format.", ephemeral=True)
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
                query = f"INSERT OR REPLACE INTO goodbye_embed (guild_id, {', '.join(updates)}) VALUES (?, {', '.join(['?'] * len(updates))})"
                values.insert(0, interaction.guild_id)
                await db.execute(query, values)
                await db.commit()
                await interaction.response.send_message("Goodbye embed updated successfully.")
            else:
                await interaction.response.send_message("No changes were made to the goodbye embed.")

    @goodbye.command(name="embed-image", description="Set the goodbye embed image")
    @app_commands.describe(url="Image URL", attachment="Uploaded image")
    async def goodbye_embed_image(self, interaction: discord.Interaction, url: str = None, attachment: discord.Attachment = None):
        """
        Set the image for the goodbye embed.

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
            await db.execute("INSERT OR REPLACE INTO goodbye_embed (guild_id, image_url) VALUES (?, ?)",
                             (interaction.guild_id, image_url))
            await db.commit()
        await interaction.response.send_message("Goodbye embed image updated successfully.")

    @goodbye.command(name="embed-thumbnail", description="Set the goodbye embed thumbnail")
    @app_commands.describe(url="Thumbnail URL", attachment="Uploaded thumbnail image")
    async def goodbye_embed_thumbnail(self, interaction: discord.Interaction, url: str = None, attachment: discord.Attachment = None):
        """
        Set the thumbnail for the goodbye embed.

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
            await db.execute("INSERT OR REPLACE INTO goodbye_embed (guild_id, thumbnail_url) VALUES (?, ?)",
                             (interaction.guild_id, thumbnail_url))
            await db.commit()
        await interaction.response.send_message("Goodbye embed thumbnail updated successfully.")

    @goodbye.command(name="message-set", description="Set the goodbye message")
    @app_commands.describe(message="The goodbye message to be sent. You can use placeholders like {user_mention}, {user_name}, {user_display_name}, {member_count}, and {guild.name}.")
    async def goodbye_message_set(self, interaction: discord.Interaction, *, message: str):
        """
        Set the goodbye message text.

        Args:
            interaction (discord.Interaction): The interaction object.
            message (str): The goodbye message text, which can include placeholders.
        """
        async with aiosqlite.connect(DB_PATH) as db:
            await db.execute("UPDATE goodbye SET goodbye_message = ? WHERE guild_id = ?",
                             (message, interaction.guild_id))
            await db.commit()
        await interaction.response.send_message("Goodbye message updated successfully.")

    @goodbye.command(name="test", description="Test the goodbye message for this server")
    async def goodbye_test(self, interaction: discord.Interaction):
        """
        Test the goodbye message and embed for the server.

        Args:
            interaction (discord.Interaction): The interaction object.
        """
        goodbye_data = await get_goodbye_data(interaction.guild_id)
        
        if not goodbye_data or not goodbye_data['goodbye_enabled']:
            return await interaction.response.send_message("Goodbye messages are not enabled for this server. Use `/goodbye enable` to get started.", ephemeral=True)

        channel = self.bot.get_channel(goodbye_data['goodbye_channel'])
        if not channel:
            return await interaction.response.send_message("The configured goodbye channel no longer exists. Please set a new channel using `/goodbye enable`.", ephemeral=True)

        embed_data = await get_goodbye_embed_data(interaction.guild_id)
        embed = discord.Embed()
        if embed_data:
            if embed_data['title']:
                embed.title = self.format_string(embed_data['title'], interaction.user)
            
            # Ensure there's always a description
            embed.description = self.format_string(embed_data['description'], interaction.user) if embed_data['description'] else f"Goodbye from {interaction.guild.name}!"
            
            if embed_data['color']:
                color = parse_color(embed_data['color'])
                if color:
                    embed.color = color
            if embed_data['footer_text']:
                embed.set_footer(text=self.format_string(embed_data['footer_text'], interaction.user), icon_url=embed_data['footer_icon_url'])
            if embed_data['author_name']:
                embed.set_author(name=self.format_string(embed_data['author_name'], interaction.user), icon_url=embed_data['author_icon_url'])
            if embed_data['image_url']:
                embed.set_image(url=embed_data['image_url'])
            if embed_data['thumbnail_url']:
                embed.set_thumbnail(url=embed_data['thumbnail_url'])
            if embed_data['timestamp']:
                embed.timestamp = discord.utils.utcnow()
        else:
            # If no embed data is found, create a default embed
            embed.title = f"Goodbye from {interaction.guild.name}!"
            embed.description = f"Farewell, {interaction.user.mention}! We hope to see you again soon."

        goodbye_message = self.format_string(goodbye_data['goodbye_message'], interaction.user)
        
        try:
            await interaction.response.send_message("Here's a preview of the goodbye message:", ephemeral=True)
            await interaction.followup.send(content=goodbye_message, embed=embed, ephemeral=True)
            await interaction.followup.send(f"The actual goodbye message will be sent in {channel.mention}.", ephemeral=True)
        except discord.HTTPException as e:
            await interaction.response.send_message(f"Error sending goodbye message preview: {e}", ephemeral=True)

    @commands.Cog.listener()
    async def on_member_remove(self, member: discord.Member):
        """
        Event listener for when a member leaves the server.
        Sends a goodbye message and embed if enabled.

        Args:
            member (discord.Member): The member who left the server.
        """
        goodbye_data = await get_goodbye_data(member.guild.id)
        if not goodbye_data or not goodbye_data['goodbye_enabled']:
            return

        channel = self.bot.get_channel(goodbye_data['goodbye_channel'])
        if not channel:
            return

        embed_data = await get_goodbye_embed_data(member.guild.id)
        embed = discord.Embed()
        if embed_data:
            if embed_data['title']:
                embed.title = self.format_string(embed_data['title'], member)
            
            # Ensure there's always a description
            embed.description = self.format_string(embed_data['description'], member) if embed_data['description'] else f"Goodbye from {member.guild.name}!"
            
            if embed_data['color']:
                embed.color = parse_color(embed_data['color'])
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
            embed.title = f"Goodbye from {member.guild.name}!"
            embed.description = f"Farewell, {member.name}! We hope to see you again soon."

        goodbye_message = self.format_string(goodbye_data['goodbye_message'], member)
        
        try:
            await channel.send(content=goodbye_message, embed=embed)
        except discord.HTTPException as e:
            print(f"Error sending goodbye message: {e}")

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

    def is_valid_url(self, url: str) -> bool:
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

async def setup(bot: commands.Bot):
    await bot.add_cog(Goodbye(bot))
    await db_setup()
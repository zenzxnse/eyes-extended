import discord, os, aiosqlite
from discord.ext import commands
from discord import app_commands

DB_PATH = "db/welcome.db"


""" 
each guild will have a different welcome message and a welcome channel
for each guild, we will have a table in the database with the following columns:
- guild_id
- welcome_message -- for welcome messages we will have seperate properties attached to it. such as embed, message, image parms, etc
- welcome_channel -- the channel to send the welcome message to can also be sent through webhook if configured.
- welcome_role -- the role to assign to the user when they join the server
"""

async def db_setup():
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("""CREATE TABLE IF NOT EXISTS welcome 
                         (guild_id INTEGER
                         welcome_enabled BOOLEAN, 
                         welcome_message TEXT, 
                         welcome_channel INTEGER, 
                         welcome_role INTEGER,
                         welcome_image TEXT --link to the image to send with the welcome message
                         welcome_embed TEXT --embed to send with the welcome message if this is enabled then image url will be displayed inside this embed.
                         welcome_webhook TEXT --webhook to send with the welcome message
                         PRIMARY KEY (guild_id)
                         )""")
        await db.execute("""CREATE TABLE IF NOT EXISTS welcome_emb
                         (guild_id INTEGER PRIMARY KEY -- for each guild welcome embed settings are different, 
                         title TEXT,
                         description TEXT,
                         image TEXT,
                         color TEXT,
                         footer_text TEXT,
                         footer_icon_url TEXT
                         author_text TEXT,
                         author_icon_url TEXT
                         timestamp BOOLEAN
                         )""")
        await db.commit()


async def welcome_emb_update(guild_id: int, title: str = None, description: str = None, image: str = None, color: str = None, footer_text: str = None, footer_icon_url: str = None, author_text: str = None, timestamp: bool = None):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("UPDATE welcome_emb SET title = ?, description = ?, image = ?, color = ?, footer_text = ?, footer_icon_url = ?, author_text = ?, timestamp = ? WHERE guild_id = ?", (title, description, image, color, footer_text, footer_icon_url, author_text, timestamp, guild_id))
        await db.commit()
        
async def enable_welcome(guild_id: int, welcome_enabled: bool):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("UPDATE welcome SET welcome_enabled = ? WHERE guild_id = ?", (welcome_enabled, guild_id))
        await db.commit()



class Welcome(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
    
    welcome = app_commands.Group(name="welcome", description="Welcome to the server")
     
    @welcome.command(name="enable", description="Enable welcome messages")
    async def welcome_enable(self, interaction: discord.Interaction, welcome_channel: discord.TextChannel):
        """ Enable the bot to start tracking on member joins in the server if the channel is not set then bot will log nothing."""
        if welcome_channel is None:
            await interaction.response.send_message("Please set a channel to send the welcome message to.")
            return
        
        
from typing import Optional
import discord
from Augmentations.Flags.element_flags import show_stats, show_top, start_game
from discord import app_commands
from discord.ext import commands
import aiosqlite
import asyncio
import os

class flags(commands.GroupCog, name='flags'):
    def __init__(self, client: commands.Bot):
        self.client = client
        self.db_path = 'db/flag_channels.db'  # Database path

    @commands.Cog.listener()
    async def on_ready(self):
        await self.create_table()  # Ensure the table is created when the bot is ready

    async def create_table(self):
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute('''
                CREATE TABLE IF NOT EXISTS flag_channels (
                    guild_id INTEGER PRIMARY KEY,
                    channel_id INTEGER NOT NULL
                )
            ''')
            await db.commit()

    async def set_flag_channel(self, guild_id: int, channel_id: Optional[int]):
        async with aiosqlite.connect(self.db_path) as db:
            # Check if the channel is already set as the flag channel
            current_channel_id = await self.get_flag_channel(guild_id)
            if current_channel_id == channel_id:
                # If the same channel is set again, remove it from the database
                await db.execute('DELETE FROM flag_channels WHERE guild_id = ?', (guild_id,))
                await db.commit()
                return False  # Indicate that the channel was removed
            else:
                # Otherwise, insert or update the channel
                await db.execute('''
                    INSERT INTO flag_channels (guild_id, channel_id) VALUES (?, ?)
                    ON CONFLICT(guild_id) DO UPDATE SET channel_id = excluded.channel_id
                ''', (guild_id, channel_id))
                await db.commit()
                return True

    async def get_flag_channel(self, guild_id: int) -> Optional[int]:
        async with aiosqlite.connect(self.db_path) as db:
            async with db.execute('SELECT channel_id FROM flag_channels WHERE guild_id = ?', (guild_id,)) as cursor:
                row = await cursor.fetchone()
                return row[0] if row else None

    async def check_flag_channel(self, interaction: discord.Interaction) -> bool:
        """Check if the interaction is in the configured flag channel."""
        flag_channel_id = await self.get_flag_channel(interaction.guild_id)
        if flag_channel_id is None:
            await interaction.response.send_message("Flag channel has not been configured.", ephemeral=True)
            return False
        if interaction.channel_id != flag_channel_id:
            await interaction.response.send_message("This command can only be used in the configured flag game channel.", ephemeral=True)
            return False
        return True

    @app_commands.command(
        name='setup_flag_channel',
        description='Sets up a channel for the game of flags.'
    )
    async def setup_flag_channel(
        self,
        interaction: discord.Interaction,
        channel: discord.TextChannel
    ):
        result = await self.set_flag_channel(interaction.guild_id, channel.id)
        if result:
            await interaction.response.send_message(f"Flag game channel set to {channel.mention}")
        else:
            await interaction.response.send_message(f"Flag game channel {channel.mention} has been removed as the game channel.", ephemeral=True)
    
    @app_commands.command(
        name = 'game',
        description = 'Lets you start a minigame of game of flags.'
    )
    @app_commands.describe(
        mode = 'Let\'s you choose between modes.'
    )
    @app_commands.choices(
        mode = [
            discord.app_commands.Choice(name = 'Europe', value = 1),
            discord.app_commands.Choice(name = 'Asia', value = 2),
            discord.app_commands.Choice(name = 'Africa', value = 3),
            discord.app_commands.Choice(name = 'America', value = 4),
        ]
    )
    @app_commands.guild_only()
    async def game(
        self,
        interaction: discord.Interaction,
        mode: int
    ):
        if not await self.check_flag_channel(interaction):
            return
        await start_game(self, interaction=interaction, mode=mode)
    
    @app_commands.command(
        name = 'statistics',
        description = 'Returns a bunch of statistics for nerds regarding the game of flags.'
    )
    @app_commands.describe(
        mode = 'Let\'s you choose between modes.',
        member = 'Member which statistics you want to see, skip to view yours.'
    )
    @app_commands.choices(
        mode = [
            discord.app_commands.Choice(name = 'Europe', value = 1),
            discord.app_commands.Choice(name = 'Asia', value = 2),
            discord.app_commands.Choice(name = 'Africa', value = 3),
            discord.app_commands.Choice(name = 'America', value = 4),
        ]
    )
    @app_commands.guild_only()
    async def statistics(
        self,
        interaction: discord.Interaction,
        mode: int,
        member: Optional[discord.Member] = None
    ):
        member = member or interaction.user

        stats = show_stats(interaction = interaction, mode=mode, member = member)
        if not await self.check_flag_channel(interaction):
            return
        await interaction.response.send_message(embed = stats)

    @app_commands.command(
        name = 'leaderboard',
        description = 'Returns the top 25 players and their streaks.'
    )
    @app_commands.describe(
        mode = 'Let\'s you choose between modes.'
    )
    @app_commands.choices(
        mode = [
            discord.app_commands.Choice(name = 'Europe', value = 1),
            discord.app_commands.Choice(name = 'Asia', value = 2),
            discord.app_commands.Choice(name = 'Africa', value = 3),
            discord.app_commands.Choice(name = 'America', value = 4),
        ]
    )
    @app_commands.guild_only()
    async def leaderboard(
        self,
        interaction: discord.Interaction,
        mode: int
    ):

        top = show_top(interaction = interaction, mode=mode)
        if not await self.check_flag_channel(interaction):
            return
        await interaction.response.send_message(embed = top)
        
async def setup(client: commands.Bot) -> None:
    await client.add_cog(flags(client))
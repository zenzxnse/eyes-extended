import discord
from discord.ext import commands
from discord import app_commands
import aiosqlite
import random
import asyncio
import math
from typing import Optional

DB_PATH = "db/leveling.db"

class LevelingSystem(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.db = None
        self.xp_cooldown = commands.CooldownMapping.from_cooldown(1, 15, commands.BucketType.member)
        self.bot.loop.create_task(self.setup_db())

    async def setup_db(self):
        self.db = await aiosqlite.connect(DB_PATH)
        await self.db.execute('''CREATE TABLE IF NOT EXISTS leveling
                                 (guild_id INTEGER, user_id INTEGER, xp INTEGER, level INTEGER,
                                 PRIMARY KEY (guild_id, user_id))''')
        await self.db.execute('''CREATE TABLE IF NOT EXISTS guild_settings
                                 (guild_id INTEGER PRIMARY KEY, enabled BOOLEAN, announce_channel INTEGER,
                                 announce_message TEXT)''')
        await self.db.commit()

    def cog_unload(self):
        asyncio.create_task(self.db.close())

    @commands.Cog.listener()
    async def on_message(self, message):
        if message.author.bot:
            return

        bucket = self.xp_cooldown.get_bucket(message)
        if bucket.update_rate_limit():
            return

        async with self.db.execute("SELECT enabled FROM guild_settings WHERE guild_id = ?", 
                                   (message.guild.id,)) as cursor:
            result = await cursor.fetchone()
            if not result or not result[0]:
                return

        xp_gain = random.randint(5, 30)
        await self.add_xp(message.guild.id, message.author.id, xp_gain)

    async def add_xp(self, guild_id, user_id, xp_amount):
        async with self.db.execute("SELECT xp, level FROM leveling WHERE guild_id = ? AND user_id = ?",
                                   (guild_id, user_id)) as cursor:
            result = await cursor.fetchone()
            if result:
                current_xp, current_level = result
                new_xp = current_xp + xp_amount
                new_level = self.calculate_level(new_xp)
                if new_level > current_level:
                    await self.level_up(guild_id, user_id, new_level)
                await self.db.execute("UPDATE leveling SET xp = ?, level = ? WHERE guild_id = ? AND user_id = ?",
                                      (new_xp, new_level, guild_id, user_id))
            else:
                new_xp = xp_amount
                new_level = self.calculate_level(new_xp)
                await self.db.execute("INSERT INTO leveling (guild_id, user_id, xp, level) VALUES (?, ?, ?, ?)",
                                      (guild_id, user_id, new_xp, new_level))
        await self.db.commit()

    def calculate_level(self, xp):
        return min(100, int((xp / 100) ** 0.5))

    def calculate_xp_for_level(self, level):
        return int(level ** 2 * 100)

    async def level_up(self, guild_id, user_id, new_level):
        guild = self.bot.get_guild(guild_id)
        if not guild:
            return
        member = guild.get_member(user_id)
        if not member:
            return

        async with self.db.execute("SELECT announce_channel, announce_message FROM guild_settings WHERE guild_id = ?",
                                   (guild_id,)) as cursor:
            result = await cursor.fetchone()
            if not result:
                return
            announce_channel_id, announce_message = result

        if announce_channel_id:
            channel = guild.get_channel(announce_channel_id)
            if channel:
                if not announce_message:
                    announce_message = "{user_mention} has reached level {level}!"
                message = announce_message.format(
                    user=member,
                    guild=guild,
                    user_mention=member.mention,
                    user_name=member.name,
                    user_display_name=member.display_name,
                    member_count=self.get_ordinal(guild.member_count),
                    level=new_level
                )
                await channel.send(message)

    def get_ordinal(self, n):
        suffix = ['th', 'st', 'nd', 'rd', 'th'][min(n % 10, 4)]
        if 11 <= (n % 100) <= 13:
            suffix = 'th'
        return f"{n}{suffix}"

    @app_commands.command(name="enable_levelling")
    @app_commands.checks.has_permissions(administrator=True)
    async def enable_levelling(self, interaction: discord.Interaction):
        """Enable levelling for this server."""
        await self.db.execute("INSERT OR REPLACE INTO guild_settings (guild_id, enabled) VALUES (?, ?)",
                              (interaction.guild_id, True))
        await self.db.commit()
        await interaction.response.send_message("Levelling has been enabled for this server.")

    @app_commands.command(name="disable_levelling")
    @app_commands.checks.has_permissions(administrator=True)
    async def disable_levelling(self, interaction: discord.Interaction):
        """Disable levelling for this server."""
        await self.db.execute("INSERT OR REPLACE INTO guild_settings (guild_id, enabled) VALUES (?, ?)",
                              (interaction.guild_id, False))
        await self.db.commit()
        await interaction.response.send_message("Levelling has been disabled for this server.")

    @app_commands.command(name="rank")
    async def rank(self, interaction: discord.Interaction, member: Optional[discord.Member] = None):
        """Display the rank of a user."""
        member = member or interaction.user
        async with self.db.execute("SELECT xp, level FROM leveling WHERE guild_id = ? AND user_id = ?",
                                   (interaction.guild_id, member.id)) as cursor:
            result = await cursor.fetchone()
            if not result:
                await interaction.response.send_message(f"{member.display_name} has not gained any XP yet.")
                return
            xp, level = result

        next_level_xp = self.calculate_xp_for_level(level + 1)
        xp_needed = next_level_xp - xp

        async with self.db.execute("SELECT COUNT(*) FROM leveling WHERE guild_id = ? AND xp > ?",
                                   (interaction.guild_id, xp)) as cursor:
            rank = (await cursor.fetchone())[0] + 1

        embed = discord.Embed(title=f"Rank for {member.display_name}", color=discord.Color.blue())
        embed.add_field(name="Level", value=str(level))
        embed.add_field(name="XP", value=f"{xp}/{next_level_xp}")
        embed.add_field(name="Rank", value=self.get_ordinal(rank))
        embed.add_field(name="XP to next level", value=str(xp_needed))
        embed.set_thumbnail(url=member.display_avatar.url)

        await interaction.response.send_message(embed=embed)

    @app_commands.command(name="add_exp")
    @app_commands.checks.has_permissions(administrator=True)
    async def add_exp(self, interaction: discord.Interaction, user: discord.Member, exp_amount: int):
        """Add experience to a user."""
        await self.add_xp(interaction.guild_id, user.id, exp_amount)
        await interaction.response.send_message(f"Added {exp_amount} XP to {user.display_name}.")

    @app_commands.command(name="add_level")
    @app_commands.checks.has_permissions(administrator=True)
    async def add_level(self, interaction: discord.Interaction, user: discord.Member, level_amount: int):
        """Add levels to a user."""
        async with self.db.execute("SELECT xp, level FROM leveling WHERE guild_id = ? AND user_id = ?",
                                   (interaction.guild_id, user.id)) as cursor:
            result = await cursor.fetchone()
            if not result:
                current_xp, current_level = 0, 0
            else:
                current_xp, current_level = result

        new_level = min(100, current_level + level_amount)
        new_xp = self.calculate_xp_for_level(new_level)

        await self.db.execute("INSERT OR REPLACE INTO leveling (guild_id, user_id, xp, level) VALUES (?, ?, ?, ?)",
                              (interaction.guild_id, user.id, new_xp, new_level))
        await self.db.commit()

        await interaction.response.send_message(f"Added {level_amount} levels to {user.display_name}. "
                                                f"They are now level {new_level}.")

    @app_commands.command(name="level_set")
    @app_commands.checks.has_permissions(administrator=True)
    async def level_set(self, interaction: discord.Interaction, user: discord.Member, new_level: int):
        """Set a user's level."""
        new_level = max(0, min(100, new_level))
        new_xp = self.calculate_xp_for_level(new_level)

        await self.db.execute("INSERT OR REPLACE INTO leveling (guild_id, user_id, xp, level) VALUES (?, ?, ?, ?)",
                              (interaction.guild_id, user.id, new_xp, new_level))
        await self.db.commit()

        await interaction.response.send_message(f"Set {user.display_name}'s level to {new_level}.")

    @app_commands.command(name="calculate")
    async def calculate(self, interaction: discord.Interaction, level: int):
        """Calculate the XP needed for a specific level."""
        if level < 0 or level > 100:
            await interaction.response.send_message("Level must be between 0 and 100.")
            return

        xp_needed = self.calculate_xp_for_level(level)
        await interaction.response.send_message(f"To reach level {level}, you need a total of {xp_needed} XP.")

    @app_commands.command(name="level_announce")
    @app_commands.checks.has_permissions(administrator=True)
    async def level_announce(self, interaction: discord.Interaction, channel: discord.TextChannel):
        """Set the channel for level up announcements."""
        await self.db.execute("INSERT OR REPLACE INTO guild_settings (guild_id, announce_channel) VALUES (?, ?)",
                              (interaction.guild_id, channel.id))
        await self.db.commit()
        await interaction.response.send_message(f"Level up announcements will now be sent in {channel.mention}.")

    @app_commands.command(name="level_announce_message")
    @app_commands.checks.has_permissions(administrator=True)
    async def level_announce_message(self, interaction: discord.Interaction, *, message: str):
        """Set the level up announcement message."""
        await self.db.execute("INSERT OR REPLACE INTO guild_settings (guild_id, announce_message) VALUES (?, ?)",
                              (interaction.guild_id, message))
        await self.db.commit()
        await interaction.response.send_message("Level up announcement message has been set.")

    @app_commands.command(name="leaderboard")
    async def leaderboard(self, interaction: discord.Interaction):
        """Display the top 10 members in the server's leveling leaderboard."""
        await interaction.response.defer()

        async with self.db.execute("""
            SELECT user_id, xp, level
            FROM leveling
            WHERE guild_id = ?
            ORDER BY xp DESC
            LIMIT 10
        """, (interaction.guild.id,)) as cursor:
            leaderboard_data = await cursor.fetchall()

        if not leaderboard_data:
            await interaction.followup.send("No leaderboard data available for this server.")
            return

        embed = discord.Embed(title=f"Leaderboard for {interaction.guild.name}", color=discord.Color.gold())
        
        for index, (user_id, xp, level) in enumerate(leaderboard_data, start=1):
            member = interaction.guild.get_member(user_id)
            if member:
                name = member.display_name
            else:
                name = f"Unknown User (ID: {user_id})"
            
            embed.add_field(
                name=f"{index}. {name}",
                value=f"Level: {level} | XP: {xp}",
                inline=False
            )

        await interaction.followup.send(embed=embed)

    

async def setup(bot):
    await bot.add_cog(LevelingSystem(bot))
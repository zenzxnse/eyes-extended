from discord.ext import commands
from discord import app_commands
import discord

def is_owner_ctx():
    async def predicate(ctx):
        if ctx.author.id == ctx.bot.owner_id:
            return True
        await ctx.send("You are not the owner of this bot.")
        return False
    return commands.check(predicate)

def is_owner_app():
    async def predicate(interaction: discord.Interaction):
        if interaction.user.id == interaction.client.owner_id:
            return True
        await interaction.response.send_message("You are not the owner of this bot.", ephemeral=True)
        return False
    return app_commands.check(predicate)

def is_server_owner():
    async def predicate(interaction: discord.Interaction):
        if interaction.guild is None:
            await interaction.response.send_message("This command can only be used in a server.", ephemeral=True)
            return False
        if interaction.user.id == interaction.guild.owner_id:
            return True
        await interaction.response.send_message("You are not the owner of this server.", ephemeral=True)
        return False
    return app_commands.check(predicate)



if __name__ == "__main__":
    print(is_owner_ctx())
    print(is_owner_app())
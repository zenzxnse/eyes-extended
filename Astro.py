from typing import Any, Optional, Type
import discord
from discord import app_commands 
from discord.ext import commands
from discord.ext.commands.help import HelpCommand
import Extensions
from Global import config
from Extensions.Utility.embed import DynamicButtonView
from Extensions.Commands.textpersistent import Testview
from colorama import Fore, Style
from Augmentations.permissions import is_owner_ctx, is_owner_app
import os

AUTO_SHARDING = False

class アストロ(commands.AutoShardedBot):
    def __init__(self, *args, **kwargs):
        if AUTO_SHARDING:
            super().__init__(*args, **kwargs)
        else:
            super().__init__(shard_count=1, *args, **kwargs)

    async def setup_hook(self):
        await Extensions.load_extensions(self)
        print(f"{Fore.GREEN}Syncing commands...{Style.RESET_ALL}")
        synced = await self.tree.sync()
        print(f"{Fore.GREEN}Synced {len(synced)} commands{Style.RESET_ALL}")
        print(f"{Fore.GREEN}Adding views...{Style.RESET_ALL}")
        dynamic_button_view = DynamicButtonView(self)
        await dynamic_button_view.load_all_buttons()  # load all buttons first
        self.add_view(dynamic_button_view)
        self.add_view(Testview())
        print(f"{Fore.GREEN}Views Added{Style.RESET_ALL}")
        
    def main(self, *args, **kwargs):
        return self.command(*args, **kwargs)
        


intents = discord.Intents.default()
intents.message_content = True
intents.guilds = True
intents.members = True
intents.reactions = True
intents.presences = True
intents.messages = True
intents.auto_moderation = True
intents.integrations = True
intents.invites = True
intents.typing = True
intents.guild_typing = True
intents.guild_messages = True
intents.guild_reactions = True
intents.guild_typing = True
intents.guild_messages = True
intents.guild_reactions = True

Eyes = アストロ(command_prefix=["*", "&"], intents=intents, help_command=None)

@Eyes.main(name="reload_cog", help="Reloads a specified cog. Usage: !reload_cog <cog_directory>", aliases=['rc'])
@commands.check(is_owner_ctx())
async def reload_cog(ctx, cog_directory: str):
    try:
        # Unload the cog first
        await Eyes.unload_extension(cog_directory)
        # Load the cog again
        await Eyes.load_extension(cog_directory)
        await ctx.send(f"```yml\n(✿◕‿◕) Successfully reloaded the cog: {cog_directory}\n```")
        # Sync the commands
        await Eyes.tree.sync()
    except commands.ExtensionNotLoaded:
        await ctx.send(f"```yml\n(￣﹏￣；) The cog {cog_directory} wasn't loaded, check your spelling retard!\n```")
    except commands.ExtensionNotFound:
        await ctx.send(f"```yml\n(￣y▽,￣)╭  That cog {cog_directory} does not exist or wasn't found.\n```")
    except Exception as e:
        await ctx.send(f"```yml\nUhh!~ 0_0 some error occurred: {str(e)}\n```")

@Eyes.main(name="reload_all", help="Reloads all cogs.", aliases=['ra'])
@commands.check(is_owner_ctx())
async def reload_all(ctx):
    loading_emoji = "🔄"
    success_emoji = "✅"
    cog_directories = COMMANDS + UTILITIES + FUN + EVENT_HANDLERS

    for cog_directory in cog_directories:
        try:
            cog_name = cog_directory.split('.')[-1]
            await ctx.send(f"{loading_emoji} Reloading cog: {cog_name}...")
            await Eyes.unload_extension(cog_directory)
            await Eyes.load_extension(cog_directory)
            await ctx.send(f"{success_emoji} Successfully reloaded cog: {cog_name}")
        except Exception as e:
            await ctx.send(f"```yml\nUhh!~ 0_0 Error reloading cog {cog_name}: {str(e)}\n```")

    # Sync the commands
    await Eyes.tree.sync()
    await ctx.send("```yml\n(✿◕‿◕) All cogs have been reloaded and commands have been synced.\n```")
    
    
@Eyes.tree.error
async def on_app_command_error(interaction: discord.Interaction, error: app_commands.AppCommandError):
    if isinstance(error, app_commands.CommandOnCooldown):
        cool_error = discord.Embed(title = f"Slow it down bro!", description = f"Try again in {error.retry_after:.2f}s.", colour = discord.Colour.light_grey())
        await interaction.response.send_message(embed = cool_error, ephemeral = True)
    elif isinstance(error, app_commands.MissingPermissions):
        missing_perm = error.missing_permissions[0].replace("_", " ").title()
        per_error = discord.Embed(title = f"You're Missing Permissions!", description = f"You don't have {missing_perm} permission.", colour = discord.Colour.light_grey())
        await interaction.response.send_message(embed = per_error, ephemeral = True)
    elif isinstance(error, app_commands.BotMissingPermissions):
        missing_perm = error.missing_permissions[0].replace("_", " ").title()
        per_error = discord.Embed(title = f"I'm Missing Permissions!", description = f"I don't have {missing_perm} permission.", colour = discord.Colour.light_grey())
        await interaction.response.send_message(embed = per_error, ephemeral = True)
    else:
        error_channel = Eyes.get_channel(int(config['ERROR_CHANNEL_ID']))
        await error_channel.send(error)
        await interaction.response.send_message(f"Sorry, an error had occured.\nIf you are facing any issues with me you can always send your </feedback:1027218853127794780>.", ephemeral = True)
        raise error



Eyes.run(config['トークン'])
import discord as dis
from discord.ext import commands as cmds
from discord import app_commands as app_cmds


class HelpDropdown(app_cmds.Select):
    def __init__(self):
        super().__init__(placeholder="Select a command", min_values=1, max_values=1)
        self.add_option(label="help", description="Get help with the bot", value="help")

    async def callback(self, interaction: dis.Interaction):
        await interaction.response.send_message(f"Selected command: {self.values[0]}")

class Help(cmds.Cog):
    def __init__(self, bot):
        self.bot = bot
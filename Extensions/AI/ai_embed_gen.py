import discord
from discord.ext import commands
from discord import app_commands


class AI_Embed_Gen(commands.GroupCog, name="Ai", description="Generate embeds using AI"):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    embed = app_commands.Group(name="embed", description="Generate embeds using AI")
    
    @embed.command(name="generate", description="Generate an embed")
    async def aiEmbedGenerate(self, interaction: discord.Interaction):
        ...

async def setup(bot: commands.Bot):
    await bot.add_cog(AI_Embed_Gen(bot))
            
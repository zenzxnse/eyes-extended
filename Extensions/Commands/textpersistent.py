import discord
from discord.ext import commands
from discord import app_commands
import asyncio

class Testview(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)
        
    @discord.ui.button(label="Test", style=discord.ButtonStyle.primary, custom_id="test_button")
    async def test(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_message("Test")

class TestExt(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        
    @commands.command()
    async def test(self, ctx: commands.Context):
        await ctx.send("Test", view=Testview())

    @commands.command()
    async def reactiontest(self, ctx: commands.Context):
        message = await ctx.send("React with a football!", view=Testview())
        await message.add_reaction("⚽")

        def check(reaction, user):
            return user != self.bot.user and str(reaction.emoji) == "⚽" and reaction.message.id == message.id

        while True:
            try:
                reaction, user = await self.bot.wait_for("reaction_add", timeout=60.0, check=check)
                await ctx.send(f"{user.name} reacted with a football!")
            except asyncio.TimeoutError:
                break

            try:
                reaction, user = await self.bot.wait_for("reaction_remove", timeout=60.0, check=check)
                await ctx.send(f"{user.name} removed the football reaction!")
            except asyncio.TimeoutError:
                break


async def setup(bot: commands.Bot):
    await bot.add_cog(TestExt(bot))


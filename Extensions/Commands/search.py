import discord
from discord.ext import commands
from Augmentations.Ai.search_with_ai import ai_internet_search, default_instructions
import re

class Ai_Search(commands.Cog):
    def __init__(self, アストロ):
        self.アストロ = アストロ

    @commands.command(name="search", description="Search the web using AI", aliases=["search_ai", "web"])
    async def ai_search(self, ctx, *, query):
        # Extract query from quotes if present
        match = re.search(r'"([^"]*)"', query)
        if match:
            query = match.group(1)
        else:
            query = query.strip()

        # Limit query to 200 characters
        query = query[:200]

        # Prepare the history with the user's query
        history = [{"role": "user", "content": query}]
        
        # Call the ai_internet_search function
        response, embed = await ai_internet_search(history)
        # Send the response back to the user
        await ctx.send(response)
        
        # Send the embed if available
        if embed:
            await ctx.send(embed=embed)

# Add the cog to the bot
async def setup(bot):
    await bot.add_cog(Ai_Search(bot))
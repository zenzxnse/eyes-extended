import discord
from discord import app_commands
from discord.ext import commands
import asyncio

class HelpView(discord.ui.View):
    def __init__(self, bot):
        super().__init__(timeout=300)
        self.bot = bot
        self.add_item(self.CategorySelect())

    class CategorySelect(discord.ui.Select):
        def __init__(self):
            options = [
                discord.SelectOption(label="General", description="General bot commands", emoji="ℹ️"),
                discord.SelectOption(label="Embeds", description="Embed creation and management", emoji="📝"),
                discord.SelectOption(label="Roles", description="Role management commands", emoji="👥"),
                discord.SelectOption(label="Games", description="Fun games to play", emoji="🎮"),
                discord.SelectOption(label="Moderation", description="Moderation tools", emoji="🛡️"),
                discord.SelectOption(label="Utility", description="Utility commands", emoji="🔧")
            ]
            super().__init__(placeholder="Select a category...", options=options)

        async def callback(self, interaction: discord.Interaction):
            category = self.values[0]
            embed = create_category_embed(category)
            await interaction.response.edit_message(embed=embed)

class Help(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="help", description="Display the help menu for 目付 (Eyes)")
    async def help(self, interaction: discord.Interaction):
        embed = discord.Embed(
            title="目付 (Eyes) Help Menu",
            description="Welcome to the help menu for 目付 (Eyes), your AI-integrated Discord bot. "
                        "Select a category from the dropdown menu below to explore commands.",
            color=discord.Color.blue()
        )
        embed.add_field(name="Quick Links", value="[GitHub Repo](https://github.com/lalozen/eyes-extended.git) | [Discord Server](https://discord.gg/fcp3sF7QG)", inline=False)
        embed.set_footer(text="Use /embed guide or /roles guide for detailed information on those features.")
        
        view = HelpView(self.bot)
        await interaction.response.send_message(embed=embed, view=view)

    @app_commands.command(name="embed_guide", description="Detailed guide on embed creation and management")
    async def embed_guide(self, interaction: discord.Interaction):
        embeds = create_embed_guide_embeds()
        view = PaginatedEmbedView(embeds)
        await interaction.response.send_message(embed=embeds[0], view=view)

    @app_commands.command(name="roles_guide", description="Detailed guide on role management")
    async def roles_guide(self, interaction: discord.Interaction):
        embeds = create_roles_guide_embeds()
        view = PaginatedEmbedView(embeds)
        await interaction.response.send_message(embed=embeds[0], view=view)

class PaginatedEmbedView(discord.ui.View):
    def __init__(self, embeds):
        super().__init__()
        self.embeds = embeds
        self.current_page = 0

    @discord.ui.button(label="Previous", style=discord.ButtonStyle.gray)
    async def previous_page(self, interaction: discord.Interaction, button: discord.ui.Button):
        self.current_page = (self.current_page - 1) % len(self.embeds)
        await interaction.response.edit_message(embed=self.embeds[self.current_page])

    @discord.ui.button(label="Next", style=discord.ButtonStyle.gray)
    async def next_page(self, interaction: discord.Interaction, button: discord.ui.Button):
        self.current_page = (self.current_page + 1) % len(self.embeds)
        await interaction.response.edit_message(embed=self.embeds[self.current_page])

def create_category_embed(category):
    embed = discord.Embed(title=f"{category} Commands", color=discord.Color.blue())
    
    if category == "General":
        embed.add_field(name="/help", value="Display this help menu", inline=False)
        embed.add_field(name="/ping", value="Check bot latency", inline=False)
    elif category == "Embeds":
        embed.add_field(name="/embed create", value="Create a new embed", inline=False)
        embed.add_field(name="/embed edit", value="Edit an existing embed", inline=False)
        embed.add_field(name="/embed show", value="Display a saved embed", inline=False)
        embed.add_field(name="/embed delete", value="Delete a saved embed", inline=False)
        embed.add_field(name="/embed guide", value="Detailed guide on embed creation", inline=False)
    elif category == "Roles":
        embed.add_field(name="/roles create", value="Create a new role menu", inline=False)
        embed.add_field(name="/roles update", value="Update an existing role menu", inline=False)
        embed.add_field(name="/roles remove", value="Remove a role menu", inline=False)
        embed.add_field(name="/roles guide", value="Detailed guide on role management", inline=False)
    elif category == "Games":
        embed.add_field(name="/tictactoe", value="Play a game of Tic-Tac-Toe", inline=False)
        embed.add_field(name="/flags", value="Play the flag guessing game", inline=False)
    elif category == "Moderation":
        embed.add_field(name="/warn", value="Warn a user", inline=False)
        embed.add_field(name="/unwarn", value="Remove a warning from a user", inline=False)
        embed.add_field(name="/warnings", value="View warnings for a user", inline=False)
    elif category == "Utility":
        embed.add_field(name="/search", value="Search the web using AI", inline=False)
        embed.add_field(name="/userinfo", value="Display information about a user", inline=False)

    return embed

def create_embed_guide_embeds():
    embeds = []
    
    # Page 1: Introduction to Embeds
    embed1 = discord.Embed(title="Embed Guide - Introduction", color=discord.Color.blue())
    embed1.add_field(name="What are Embeds?", value="Embeds are rich content blocks that can contain formatted text, images, and more. They're a powerful way to present information in Discord.", inline=False)
    embed1.add_field(name="Creating an Embed", value="Use `/embed create` to start the embed creation process. You'll be guided through setting the title, description, color, and fields.", inline=False)
    embeds.append(embed1)

    # Page 2: Advanced Embed Features
    embed2 = discord.Embed(title="Embed Guide - Advanced Features", color=discord.Color.blue())
    embed2.add_field(name="Adding Fields", value="Fields allow you to organize information in columns. Use `/embed field-add` to add fields to your embed.", inline=False)
    embed2.add_field(name="Custom Buttons", value="You can add custom buttons to your embeds using the embed builder. These can link to websites or trigger bot actions.", inline=False)
    embed2.add_field(name="Webhook Integration", value="For advanced users, embeds can be sent through webhooks for more customization options.", inline=False)
    embeds.append(embed2)

    # Page 3: Managing Embeds
    embed3 = discord.Embed(title="Embed Guide - Management", color=discord.Color.blue())
    embed3.add_field(name="Editing Embeds", value="Use `/embed edit` to modify existing embeds. You can change any part of the embed, including adding or removing fields.", inline=False)
    embed3.add_field(name="Displaying Embeds", value="The `/embed show` command allows you to display your saved embeds in any channel.", inline=False)
    embed3.add_field(name="Deleting Embeds", value="If you no longer need an embed, use `/embed delete` to remove it from the bot's storage.", inline=False)
    embeds.append(embed3)

    return embeds

def create_roles_guide_embeds():
    embeds = []
    
    # Page 1: Introduction to Role Management
    embed1 = discord.Embed(title="Roles Guide - Introduction", color=discord.Color.green())
    embed1.add_field(name="Role Menus", value="Role menus allow users to self-assign roles through a dropdown interface.", inline=False)
    embed1.add_field(name="Creating a Role Menu", value="Use `/roles create rolemenu` to start creating a new role menu. You'll set a name, placeholder text, and options for role selection.", inline=False)
    embeds.append(embed1)

    # Page 2: Configuring Role Menus
    embed2 = discord.Embed(title="Roles Guide - Configuration", color=discord.Color.green())
    embed2.add_field(name="Adding Roles", value="After creating a menu, use `/roles update` to add roles to the menu. You can specify emojis and descriptions for each role.", inline=False)
    embed2.add_field(name="Setting Limits", value="You can set minimum and maximum numbers of roles a user can select from the menu.", inline=False)
    embed2.add_field(name="Customizing Appearance", value="Customize the menu's appearance with a unique name and placeholder text to guide users.", inline=False)
    embeds.append(embed2)

    # Page 3: Managing and Using Role Menus
    embed3 = discord.Embed(title="Roles Guide - Usage and Management", color=discord.Color.green())
    embed3.add_field(name="Displaying Role Menus", value="Use the `/roles` command to display a role menu for users to interact with.", inline=False)
    embed3.add_field(name="Updating Menus", value="You can update existing menus with `/roles update`, allowing you to add, remove, or modify roles.", inline=False)
    embed3.add_field(name="Removing Menus", value="If a menu is no longer needed, use `/roles remove rolemenu` to delete it entirely.", inline=False)
    embed3.add_field(name="Integration with Embeds", value="Role menus can be integrated into custom embeds for a seamless user experience.", inline=False)
    embeds.append(embed3)

    return embeds

async def setup(bot):
    await bot.add_cog(Help(bot))
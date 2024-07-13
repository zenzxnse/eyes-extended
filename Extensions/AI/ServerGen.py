import os
import discord
from discord.ext import commands
from discord import app_commands
from Augmentations.Ai.Gen_server import gen_server
from Augmentations.Optimizations.Execute_template import show_template, execute_template, delete_current_template, rep_to_dict, process_template

class ServerGen(commands.Cog):
    def __init__(self, bot):
        """
        Initializes the ServerGen object with the given bot instance, loads default and community themes,
        and sets the last generated template to None.

        Parameters:
            bot: The Discord bot instance.

        Return:
            None
        """
        self.bot = bot
        self.default_themes = self.load_themes('DT')
        self.community_themes = self.load_themes('CT')
        self.last_generated_template = None  

    def load_themes(self, folder):
        themes = {}
        path = f'Augmentations/Ai/{folder}'
        for file in os.listdir(path):
            if file.endswith('.txt'):
                themes[file[:-4]] = os.path.join(path, file)
        return themes

    async def category_autocomplete(self, interaction: discord.Interaction, current: str) -> list[app_commands.Choice[str]]:
        categories = interaction.guild.categories
        return [
            app_commands.Choice(name=category.name, value=str(category.id))
            for category in categories if current.lower() in category.name.lower()
        ][:25]  # limiting to discord's limit

    async def default_theme_autocomplete(self, interaction: discord.Interaction, current: str) -> list[app_commands.Choice[str]]:
        return [
            app_commands.Choice(name=theme, value=theme)
            for theme in self.default_themes if current.lower() in theme.lower()
        ][:25]

    async def community_theme_autocomplete(self, interaction: discord.Interaction, current: str) -> list[app_commands.Choice[str]]:
        return [
            app_commands.Choice(name=theme, value=theme)
            for theme in self.community_themes if current.lower() in theme.lower()
        ][:25]

    @app_commands.command(name="generate", description="Generate a server template using AI")
    @app_commands.checks.has_permissions(administrator=True)
    @app_commands.autocomplete(category_to_ignore=category_autocomplete)
    @app_commands.autocomplete(default_theme=default_theme_autocomplete)
    @app_commands.autocomplete(community_theme=community_theme_autocomplete)
    async def make_server(
        self, 
        interaction: discord.Interaction, 
        template_description: str, 
        verification_channel: bool = False,
        category_to_ignore: str = None,
        default_theme: str = None,
        community_theme: str = None
    ):
        await interaction.response.defer(thinking=True)

        if community_theme and default_theme:
            await interaction.followup.send("Please select either a default theme or a community theme, not both.")
            return

        if community_theme and 'COMMUNITY' not in interaction.guild.features:
            await interaction.followup.send("Community features are not enabled for this server. Please enable community features before using a community theme.")
            return

        theme = None
        if community_theme:
            theme = self.community_themes.get(community_theme)
        elif default_theme:
            theme = self.default_themes.get(default_theme)

        if not theme:
            await interaction.followup.send("Invalid theme selected. Please try again.")
            return

        print(f"Generating server template for: {template_description}")
        ai_response = await gen_server([{"role": "user", "content": template_description}], instructions=theme)
        print("AI response received")
        print(f"AI response: {ai_response}")

        self.last_generated_template = ai_response  # Store the generated template

        template_dict = rep_to_dict(ai_response)
        print("AI response converted to dictionary")
        print(f"Template dictionary: {template_dict}")

        embed, view, formatted_template = await show_template(ai_response, verification_channel)
        await interaction.followup.send(embed=embed, view=view)
        print("Template shown to user")

        view.template = template_dict
        view.verification_channel = verification_channel
        view.interaction = interaction
        view.category_to_ignore = category_to_ignore
        view.is_community = bool(community_theme)
        view.original_description = template_description
        view.original_template = self.last_generated_template  # Add this line to pass the original template

        async def on_timeout():
            await interaction.followup.send("Template confirmation timed out. Please try again.")
            print("Template confirmation timed out")

        view.on_timeout = on_timeout

        await view.wait()

        if view.value:
            print("User confirmed template, processing...")
            await process_template(interaction, template_dict, verification_channel, category_to_ignore, view.is_community)
        else:
            await interaction.followup.send("Template generation cancelled.")
            print("Template generation cancelled by user")

async def setup(bot):
    await bot.add_cog(ServerGen(bot))
import discord
from discord.ext import commands
from discord import app_commands
from Augmentations.Ai.Gen_server import gen_server
from Augmentations.Optimizations.Execute_template import show_template, execute_template, delete_current_template, rep_to_dict, process_template

class ServerGen(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="generate", description="Generate a server template using AI")
    @app_commands.checks.has_permissions(administrator=True)
    async def make_server(self, interaction: discord.Interaction, template_description: str, verification_channel: bool = False):
        await interaction.response.defer(thinking=True)

        print(f"Generating server template for: {template_description}")
        # Generate server template using AI
        ai_response = await gen_server([{"role": "user", "content": template_description}])
        print("AI response received")
        print(f"AI response: {ai_response}")  # Print the AI response

        # Convert AI response to dictionary
        template_dict = rep_to_dict(ai_response)
        print("AI response converted to dictionary")
        print(f"Template dictionary: {template_dict}")  # Print the template dictionary

        # Show the template to the user
        embed, view = await show_template(ai_response, verification_channel)
        await interaction.followup.send(embed=embed, view=view)
        print("Template shown to user")

        # Store the template and verification_channel flag in the view for later use
        view.template = template_dict
        view.verification_channel = verification_channel
        view.interaction = interaction

        async def on_timeout():
            await interaction.followup.send("Template confirmation timed out. Please try again.")
            print("Template confirmation timed out")

        view.on_timeout = on_timeout

        # Wait for user confirmation
        await view.wait()

        if view.value:
            print("User confirmed template, processing...")
            await process_template(interaction, template_dict, verification_channel)
        else:
            await interaction.followup.send("Template generation cancelled.")
            print("Template generation cancelled by user")

async def setup(bot):
    await bot.add_cog(ServerGen(bot))
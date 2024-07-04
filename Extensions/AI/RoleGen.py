import discord
from discord.ext import commands
from discord import app_commands
from Augmentations.Ai.Gen_role import gen_role
from Augmentations.Optimizations.Role_Creation import (
    show_roles, execute_roles, role_rep_to_dict, 
    delete_roles_efficiently, DeleteConfirmView
)

class RoleGen(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="generate_roles", description="Generate roles using AI")
    async def generate_roles(self, interaction: discord.Interaction, roles_description: str):
        await interaction.response.defer()
        
        print(f"Generating roles based on description: {roles_description}")
        ai_response = await gen_role([{"role": "user", "content": f"Generate roles based on this description: {roles_description}"}])
        
        print("AI response received:")
        print(ai_response)  # Print the full AI response
        
        print("Converting to role dictionary...")
        roles_dict = role_rep_to_dict(ai_response)
        
        print("Showing roles to user...")
        embed, view = await show_roles(ai_response)
        await interaction.followup.send(embed=embed, view=view)
        
        view.roles = roles_dict
        view.interaction = interaction
        
        print("Waiting for user confirmation...")
        await view.wait()
        
        if view.value:
            print("User confirmed. Executing role creation...")
            await execute_roles(interaction.guild, roles_dict)
            await interaction.followup.send("Roles have been created successfully!")
        else:
            print("Role generation cancelled by user.")
            await interaction.followup.send("Role generation cancelled.")

    @app_commands.command(name="delete-all-roles", description="Delete all deletable roles in the server")
    @app_commands.checks.has_permissions(manage_roles=True)
    async def delete_all_roles(self, interaction: discord.Interaction):
        await interaction.response.defer(thinking=True)

        if interaction.user.id != interaction.guild.owner_id:
            print("Non-owner attempted to delete all roles.")
            await interaction.followup.send("Only the server owner can use this command.")
            return

        confirm_view = DeleteConfirmView()
        await interaction.followup.send("Are you sure you want to delete all roles? This action cannot be undone.", view=confirm_view)
        
        await confirm_view.wait()
        
        if confirm_view.value:
            print("Starting deletion of all roles...")
            deleted_count, skipped_count = await delete_roles_efficiently(interaction.guild)
            await interaction.followup.send(f"Role deletion complete.\nDeleted roles: {deleted_count}\nSkipped roles: {skipped_count}")
        else:
            await interaction.followup.send("Role deletion cancelled.")

async def setup(bot):
    await bot.add_cog(RoleGen(bot))
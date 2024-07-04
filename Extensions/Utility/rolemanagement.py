import discord
from discord.ext import commands
from discord import app_commands

class RoleManagement(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        
    def extract_role_id(self, role_mention: str) -> int:
        # Extract the role ID from a mention string like "<@&1234567890>"
        return int(role_mention.strip("<@&>"))
    def get_role_permissions_and_color(self, role_type: str):
    # Define default permissions for different role types
        permissions_dict = {
            "default": discord.Permissions(),
            "trial_mod": discord.Permissions(moderate_members=True, mute_members=True, deafen_members=True, move_members=True, attach_files=True, add_reactions=True, use_external_emojis=True, change_nickname=True), 
            "mod": discord.Permissions(kick_members=True, ban_members=True, manage_messages=True, moderate_members=True, mute_members=True, deafen_members=True, move_members=True, attach_files=True, add_reactions=True, use_external_emojis=True, change_nickname=True),
            "admin": discord.Permissions(administrator=True),
            "staff": discord.Permissions(kick_members=True, ban_members=True, manage_roles=True, manage_channels=True, view_audit_log=True, move_members=True, moderate_members=True, manage_messages=True, use_application_commands=True, mute_members=True, deafen_members=True, attach_files=True, add_reactions=True, use_external_emojis=True, change_nickname=True)
        }
        # Define color for different role types
        color_dict = {
            "default": discord.Color.default(),
            "trial_mod": discord.Color.blue(),
            "mod": discord.Color.green(),
            "admin": discord.Color.red(),
            "staff": discord.Color.purple()
        }
        permissions = permissions_dict.get(role_type, discord.Permissions())
        color = color_dict.get(role_type, discord.Color.default())
        return permissions, color
    @app_commands.command(name="create_role", description="Creates a role with specified options.")
    @app_commands.describe(
        rolename="The name of the role to create.",
        put_after="The role to place the new role after. (Optional)",
        put_before="The role to place the new role before. (Optional)",
        roletype="Type of the role with predefined permissions and color."
    )
    @app_commands.choices(roletype=[
        app_commands.Choice(name="default", value="default"),
        app_commands.Choice(name="trial_mod", value="trial_mod"),
        app_commands.Choice(name="mod", value="mod"),
        app_commands.Choice(name="admin", value="admin"),
        app_commands.Choice(name="staff", value="staff")
    ])
    @app_commands.guild_only()
    async def create_role(self, interaction: discord.Interaction, rolename: str, roletype: str, put_after: str = None, put_before: str = None):
        await interaction.response.defer(ephemeral=True)

        if put_after and put_before:
            await interaction.followup.send("Please specify only one of 'put_after' or 'put_before'.")
            return

        guild = interaction.guild
        bot_member = guild.get_member(self.bot.user.id)
        bot_highest_role_position = bot_member.top_role.position

        permissions, color = self.get_role_permissions_and_color(roletype)

        target_role = None
        if put_after:
            target_role = guild.get_role(self.extract_role_id(put_after))
            if target_role and target_role.position >= bot_highest_role_position:
                await interaction.followup.send("Cannot place the new role after a role higher or equal to the bot's highest role.")
                return
        elif put_before:
            target_role = guild.get_role(self.extract_role_id(put_before))
            if target_role and target_role.position >= bot_highest_role_position:
                await interaction.followup.send("Cannot place the new role before a role higher or equal to the bot's highest role.")
                return

        if (put_after or put_before) and not target_role:
            await interaction.followup.send("Specified role not found.")
            return

        try:
            new_role = await guild.create_role(name=rolename, color=color, permissions=permissions, reason="Role created via /create_role command.")
            if target_role:
                if put_after:
                    positions = {new_role: target_role.position}
                else:  # put_before
                    positions = {new_role: target_role.position + 1}
                await guild.edit_role_positions(positions, reason="Setting role position via /create_role command.")
            await interaction.followup.send(f"Role '{rolename}' created successfully with {roletype} permissions and color.")
        except discord.errors.Forbidden:
            await interaction.followup.send("I don't have permission to create or move roles.")
        except Exception as e:
            await interaction.followup.send(f"Failed to create role: {e}")

    
            
async def setup(bot: commands.Bot):
    await bot.add_cog(RoleManagement(bot))
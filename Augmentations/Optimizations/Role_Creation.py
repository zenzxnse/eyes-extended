import discord
import re
import asyncio, aiohttp
from discord.ext import commands
from Augmentations.Ai.Gen_role import gen_role
from typing import Optional

class ConfirmView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=300)
        self.value = None
        self.roles = None
        self.interaction = None

    @discord.ui.button(label="Confirm", style=discord.ButtonStyle.green)
    async def confirm(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.defer()
        self.value = True
        self.stop()

    @discord.ui.button(label="Cancel", style=discord.ButtonStyle.red)
    async def cancel(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.defer()
        self.value = False
        self.stop()



def role_rep_to_dict(ai_response: str) -> dict:
    print("Converting AI response to role dictionary...")
    roles_dict = {"Roles": []}
    pattern = r"Role: {name: (.+)} {Hex: (#[0-9A-Fa-f]{6})} {permission: (.+)}"
    matches = re.findall(pattern, ai_response)
    
    for name, hex_color, permission in matches:
        role_info = {
            "name": name,
            "color": int(hex_color[1:], 16),
            "permission": permission
        }
        roles_dict["Roles"].append(role_info)
        print(f"Added role: {name}")
    
    print("Role dictionary creation complete.")
    return roles_dict

async def show_roles(ai_response: str):
    print("Preparing to show generated roles...")
    embed = discord.Embed(title="Generated Roles", color=discord.Color.blue())
    
    # Extract categories and roles
    categories = re.findall(r"\*\*(.*?)\*\*", ai_response)
    roles = re.findall(r"Role: {name: (.+)} {Hex: (#[0-9A-Fa-f]{6})} {permission: (.+)}", ai_response)
    
    if categories:
        # If categories are found, display roles under their respective categories
        for category in categories:
            category_roles = []
            for role in roles:
                role_index = ai_response.index(f"Role: {{name: {role[0]}}}")
                category_index = ai_response.index(f"**{category}**")
                next_category_index = len(ai_response)
                if category != categories[-1]:
                    next_category_index = ai_response.index(f"**{categories[categories.index(category)+1]}**")
                
                if category_index < role_index < next_category_index:
                    category_roles.append(role)
            
            if category_roles:
                role_list = "\n".join([f"• {role[0]} - {role[2].capitalize()} ({role[1]})" for role in category_roles])
                embed.add_field(name=category, value=role_list, inline=False)
    else:
        # If no categories are found, display all roles under a single "Roles" category
        role_list = "\n".join([f"• {role[0]} - {role[2].capitalize()} ({role[1]})" for role in roles])
        embed.add_field(name="Roles", value=role_list, inline=False)
    
    total_roles = len(roles)
    embed.set_footer(text=f"Total Roles: {total_roles}")
    
    view = ConfirmView()
    print("Roles embed and view created.")
    return embed, view

async def create_roles(guild: discord.Guild, roles_dict: dict):
    print("Starting bulk role creation process...")
    all_roles = []
    for category, roles in roles_dict.items():
        for role in roles:
            permissions = discord.Permissions()
            if role['permission'] == 'admin':
                permissions.update(administrator=True)
            elif role['permission'] == 'mod':
                permissions.update(kick_members=True, ban_members=True, manage_messages=True, 
                                   moderate_members=True, mute_members=True, deafen_members=True, 
                                   move_members=True, attach_files=True, add_reactions=True, 
                                   use_external_emojis=True, change_nickname=True)
            elif role['permission'] == 'trial_mod':
                permissions.update(moderate_members=True, mute_members=True, deafen_members=True, 
                                   move_members=True, attach_files=True, add_reactions=True, 
                                   use_external_emojis=True, change_nickname=True)
            elif role['permission'] == 'staff':
                permissions.update(kick_members=True, ban_members=True, manage_roles=True, 
                                   manage_channels=True, view_audit_log=True, move_members=True,
                                   moderate_members=True, manage_messages=True, use_application_commands=True, 
                                   mute_members=True, deafen_members=True, attach_files=True, 
                                   add_reactions=True, use_external_emojis=True, change_nickname=True)
            
            all_roles.append({
                "name": role['name'],
                "color": discord.Colour(role['color']),
                "permissions": permissions,
                "hoist": True if role['permission'] in ['admin', 'mod', 'trial_mod', 'staff'] else False,
                "mentionable": True
            })

    return all_roles

async def execute_roles(guild: discord.Guild, roles_dict: dict):
    print("Starting role creation process...")
    all_roles = await create_roles(guild, roles_dict)
    
    created_roles = []
    chunk_size = 4  # Create 4 roles at a time
    for i in range(0, len(all_roles), chunk_size):
        chunk = all_roles[i:i+chunk_size]
        tasks = [guild.create_role(**role) for role in chunk]
        created_chunk = await asyncio.gather(*tasks)
        created_roles.extend(created_chunk)
        print(f"Created {len(created_chunk)} roles. Total: {len(created_roles)}/{len(all_roles)}")
        if i + chunk_size < len(all_roles):
            await asyncio.sleep(0.5)  # Wait 1 second between batches

    print(f"Bulk role creation process complete. Created {len(created_roles)} roles.")
    return created_roles

async def delete_roles_efficiently(guild: discord.Guild):
    print("Starting efficient role deletion process...")
    deletable_roles = [role for role in guild.roles if role != guild.default_role and role.position < guild.me.top_role.position]
    
    chunk_size = 4  # Delete 4 roles at a time
    deleted_count = 0
    skipped_count = 0

    for i in range(0, len(deletable_roles), chunk_size):
        chunk = deletable_roles[i:i+chunk_size]
        delete_tasks = [role.delete() for role in chunk]
        try:
            results = await asyncio.gather(*delete_tasks, return_exceptions=True)
            for result in results:
                if isinstance(result, Exception):
                    skipped_count += 1
                    print(f"Failed to delete role: {result}")
                else:
                    deleted_count += 1
            print(f"Deleted {deleted_count} roles. Skipped: {skipped_count}")
        except discord.HTTPException as e:
            print(f"HTTP Exception while deleting roles: {e}")
            skipped_count += len(chunk)
        
        await asyncio.sleep(1)  # Wait 0.5 seconds between batches
    
    print(f"Role deletion complete. Deleted: {deleted_count}, Skipped: {skipped_count}")
    return deleted_count, skipped_count 


class DeleteConfirmView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=60)
        self.value = None

    @discord.ui.button(label="Confirm", style=discord.ButtonStyle.danger)
    async def confirm(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.defer()
        self.value = True
        self.stop()

    @discord.ui.button(label="Cancel", style=discord.ButtonStyle.secondary)
    async def cancel(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.defer()
        self.value = False
        self.stop()

async def create_chunk_roles(interaction: discord.Interaction, roles_description: str, put_after: Optional[discord.Role] = None, put_before: Optional[discord.Role] = None):
    print(f"Generating chunk roles based on description: {roles_description}")
    ai_response = await gen_role([{"role": "user", "content": f"Generate roles based on this description: {roles_description}"}])
    
    print("AI response received:")
    print(ai_response)
    
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
        print("User confirmed. Executing chunk role creation...")
        created_roles = await execute_chunk_roles(interaction.guild, roles_dict, put_after, put_before)
        return created_roles, len(created_roles)
    else:
        print("Chunk role generation cancelled by user.")
        return None, 0

async def execute_chunk_roles(guild: discord.Guild, roles_dict: dict, put_after: Optional[discord.Role] = None, put_before: Optional[discord.Role] = None):
    print("Starting chunk role creation process...")
    all_roles = await create_roles(guild, roles_dict)
    
    bot_member = guild.get_member(guild.me.id)
    bot_highest_role_position = bot_member.top_role.position

    if put_after:
        target_position = put_after.position + 1
    elif put_before:
        target_position = put_before.position
    else:
        target_position = 1  # Default to just above @everyone

    print(f"Target position: {target_position}")
    print(f"Bot's highest role position: {bot_highest_role_position}")

    if target_position >= bot_highest_role_position:
        raise ValueError("Cannot place roles higher than or equal to the bot's highest role.")

    created_roles = []
    chunk_size = 3  # Create 3 roles at a time
    for i in range(0, len(all_roles), chunk_size):
        chunk = all_roles[i:i+chunk_size]
        chunk_created_roles = []
        
        for role in chunk:
            try:
                new_role = await guild.create_role(**role)
                chunk_created_roles.append(new_role)
                print(f"Created role: {new_role.name} (ID: {new_role.id})")
            except discord.HTTPException as e:
                print(f"Failed to create role {role['name']}: {e}")
        
        created_roles.extend(chunk_created_roles)
        print(f"Created {len(chunk_created_roles)} roles. Total: {len(created_roles)}/{len(all_roles)}")
        
        if i + chunk_size < len(all_roles):
            await asyncio.sleep(0.5)  # Wait 0.5 seconds between chunks
    
    # Position all roles at once
    role_positions = []
    for index, role in enumerate(created_roles):
        role_positions.append({
            'id': role.id,
            'position': target_position + index
        })

    try:
        await guild.edit_role_positions(role_positions)
        print(f"Positioned {len(role_positions)} roles successfully.")
    except discord.HTTPException as e:
        print(f"Failed to position roles: {e}")

    print(f"Chunk role creation process complete. Created and positioned {len(created_roles)} roles.")
    return created_roles
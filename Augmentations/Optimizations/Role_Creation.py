import discord
import re
import asyncio, aiohttp
from discord.ext import commands

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
    roles_dict = {}
    pattern = r"Role: {name: (.+)} {Hex: (#[0-9A-Fa-f]{6})} {permission: (.+)}"
    matches = re.findall(pattern, ai_response)
    
    # Extract categories
    categories = re.findall(r"\*\*(.*?)\*\*", ai_response)
    
    # If no categories are found, create a default category
    if not categories:
        categories = ["Generated Roles"]
    
    for category in categories:
        roles_dict[category] = []
    
    current_category = categories[0]  # Set the initial category
    
    for name, hex_color, permission in matches:
        # If there's only one category, use it for all roles
        if len(categories) == 1:
            current_category = categories[0]
        else:
            # Find the category for this role
            for i, category in enumerate(categories):
                if ai_response.index(f"Role: {{name: {name}}}") > ai_response.index(f"**{category}**"):
                    current_category = category
        
        roles_dict[current_category].append({
            "name": name,
            "color": int(hex_color[1:], 16),
            "permission": permission
        })
        print(f"Added role: {name} to category: {current_category}")
    
    print("Role dictionary creation complete.")
    return roles_dict

async def show_roles(ai_response: str):
    print("Preparing to show generated roles...")
    embed = discord.Embed(title="Generated Roles", color=discord.Color.blue())
    
    # Extract categories and roles
    categories = re.findall(r"\*\*(.*?)\*\*", ai_response)
    roles = re.findall(r"Role: {name: (.+)} {Hex: (#[0-9A-Fa-f]{6})} {permission: (.+)}", ai_response)
    
    # If no categories are found, create a default category
    if not categories:
        categories = ["Generated Roles"]
    
    for category in categories:
        category_roles = []
        for role in roles:
            if len(categories) == 1 or categories.index(category) == len(categories) - 1 or \
               (ai_response.index(f"Role: {{name: {role[0]}}}") > ai_response.index(f"**{category}**") and 
                (categories.index(category) == len(categories) - 1 or 
                 ai_response.index(f"Role: {{name: {role[0]}}}") < ai_response.index(f"**{categories[categories.index(category)+1]}**"))):
                category_roles.append(role)
        
        if category_roles:
            role_list = "\n".join([f"• {role[0]} - {role[2].capitalize()} ({role[1]})" for role in category_roles])
            embed.add_field(name=category, value=role_list, inline=False)
    
    total_roles = len(roles)
    embed.set_footer(text=f"Total Roles: {total_roles}")
    
    view = ConfirmView()
    print("Roles embed and view created.")
    return embed, view

async def create_roles(guild: discord.Guild, roles_dict: dict, put_after: discord.Role = None, put_before: discord.Role = None):
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

async def execute_roles(guild: discord.Guild, roles_dict: dict, put_after: discord.Role = None, put_before: discord.Role = None):
    print("Starting role creation process...")
    all_roles = await create_roles(guild, roles_dict)
    
    if put_after:
        position = put_after.position + 1
    elif put_before:
        position = put_before.position
    else:
        position = 1  # Default to just above @everyone

    created_roles = []
    for role in all_roles:
        try:
            created_role = await guild.create_role(**role)
            await created_role.edit(position=position)
            created_roles.append(created_role)
            print(f"Created and positioned role: {created_role.name} at position {position}")
            position += 1
            await asyncio.sleep(0.5)  # Wait 0.5 seconds between role creations
        except discord.HTTPException as e:
            print(f"Failed to create or position role {role['name']}: {e}")
    
    print(f"Role creation process complete. Created {len(created_roles)} roles.")
    return created_roles

async def position_roles(guild: discord.Guild, created_roles: list, put_after: discord.Role = None, put_before: discord.Role = None):
    print("Positioning roles...")
    bot_member = guild.get_member(guild.me.id)
    bot_highest_role_position = bot_member.top_role.position

    if put_after:
        role_position = put_after.position + 1
    elif put_before:
        role_position = put_before.position
    else:
        return  # No positioning needed

    if role_position >= bot_highest_role_position:
        print("Cannot place the new roles after or before a role higher or equal to the bot's highest role.")
        return

    try:
        for i, role in enumerate(reversed(created_roles)):
            new_position = role_position + i
            if new_position < bot_highest_role_position:
                await role.edit(position=new_position, reason="Setting role position via generate_roles command.")
                print(f"Positioned role {role.name} at position {new_position}")
            else:
                print(f"Skipped positioning role {role.name} as it would be higher than the bot's highest role")
        print("Roles positioned successfully")
    except discord.HTTPException as e:
        print(f"Failed to position roles: {e}")

    print("Role positioning complete.")

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
        
        await asyncio.sleep(0.5)  # Wait 0.5 seconds between batches
    
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


import discord
from discord.ext import commands
import re

class ConfirmView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=300)
        self.value = None

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


def rep_to_dict(ai_response):
    template_dict = {}
    current_category = None
    for line in ai_response.split('\n'):
        if line.startswith('**') and line.endswith('**'):
            current_category = line.strip('**')
            template_dict[current_category] = []
        elif line.startswith('- '):
            if current_category is not None:
                channel_info = line[2:].split(':')
                channel_type = channel_info[0].strip()
                channel_name = channel_info[1].strip()
                flags = re.findall(r'\((.*?)\)', channel_name)
                channel_name = re.sub(r'\s*\(.*?\)', '', channel_name).strip()
                template_dict[current_category].append({
                    'type': channel_type,
                    'name': channel_name,
                    'flags': flags
                })
    print(f"Template dictionary: {template_dict}")
    return template_dict
    

async def show_template(ai_response: str, verification_channel: bool):
    formatted_template = f"```\n{ai_response}\n```"
    
    embed = discord.Embed(title="Server Template", description=f"Here's the generated server template:\n{formatted_template}\n", color=discord.Color.blue())
    embed.add_field(name="Verification System", value="Enabled" if verification_channel else "Disabled", inline=False)
    
    view = ConfirmView()
    return embed, view

async def delete_current_template(guild: discord.Guild):
    print("Deleting current channels...")
    for channel in guild.channels:
        if channel != guild.system_channel:  # Don't delete the system channel
            try:
                await channel.delete()
                print(f"Deleted channel: {channel.name}")
            except discord.Forbidden:
                print(f"Failed to delete channel {channel.name}: Forbidden")
            except discord.HTTPException as e:
                print(f"Failed to delete channel {channel.name}: {e}")
    print("Finished deleting channels")

async def execute_template(guild: discord.Guild, template_dict: dict, verification_channel: bool):
    print("Executing template...")
    print(f"Template dictionary: {template_dict}")  # Print the template dictionary
    # Create "Verified Members" role if verification_channel is True
    verified_role = None
    if verification_channel:
        verified_role = await guild.create_role(name="Verified Members")
        print("Created 'Verified Members' role")

    for category_name, channels in template_dict.items():
        print(f"Creating category: {category_name}")
        category = await guild.create_category(category_name)
        
        for channel in channels:
            channel_type = channel['type']
            channel_name = channel['name']
            flags = channel['flags']
            
            print(f"Creating {channel_type}: {channel_name}")
            if channel_type == "Voice":
                new_channel = await guild.create_voice_channel(channel_name, category=category)
            else:
                new_channel = await guild.create_text_channel(channel_name, category=category)
            
            # Set permissions
            if "Private" in flags:
                await new_channel.set_permissions(guild.default_role, view_channel=False)
                await new_channel.set_permissions(guild.me, view_channel=True)
                print(f"Set {channel_name} as Private")
            elif "Read_Only" in flags:
                await new_channel.set_permissions(guild.default_role, send_messages=False, add_reactions=False, create_public_threads=False)
                print(f"Set {channel_name} as Read_Only")
            elif "Mod_Only" in flags:
                await new_channel.set_permissions(guild.default_role, view_channel=False)
                mod_role = discord.utils.get(guild.roles, permissions=discord.Permissions(moderate_members=True))
                if mod_role:
                    await new_channel.set_permissions(mod_role, view_channel=True)
                print(f"Set {channel_name} as Mod_Only")

    if verification_channel:
        print("Setting up verification system")
        verify_category = await guild.create_category("Verification", position=0)
        verify_channel = await guild.create_text_channel("verify", category=verify_category)
        await verify_channel.set_permissions(guild.default_role, read_messages=True, send_messages=True)
        await verify_channel.set_permissions(verified_role, view_channel=False)
        
        for channel in guild.channels:
            if channel != verify_channel:
                await channel.set_permissions(guild.default_role, view_channel=False)
                await channel.set_permissions(verified_role, view_channel=True)
        print("Verification system set up complete")

    print("Template execution complete")

async def process_template(interaction: discord.Interaction, template_dict: dict, verification_channel: bool):
    guild = interaction.guild
    if not guild:
        await interaction.followup.send("This command can only be used in a server.")
        print("Command attempted outside of a server")
        return

    if interaction.user.id != guild.owner_id:
        await interaction.followup.send("Only the server owner can use this command.")
        print(f"Non-owner {interaction.user.id} attempted to use the command")
        return

    print("Starting template processing")
    try:
        await interaction.followup.send("Deleting current channels...")
    except discord.errors.HTTPException:
        print("Failed to send followup message. Continuing with template processing.")

    await delete_current_template(guild)

    try:
        await interaction.followup.send("Executing new template...")
    except discord.errors.HTTPException:
        print("Failed to send followup message. Continuing with template execution.")

    await execute_template(guild, template_dict, verification_channel)

    try:
        await interaction.followup.send("Server template has been successfully applied!")
    except discord.errors.HTTPException:
        print("Failed to send final followup message. Template processing complete.")

    print("Template processing complete")
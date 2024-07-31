import discord
from discord.ext import commands
import re
from collections import defaultdict
import asyncio, datetime
from Augmentations.Ai.Gen_server import gen_server
from Extensions.Utility.welcome import Welcome
from Extensions.Utility.goodbye import Goodbye
from Extensions.Utility.welcome import DB_PATH as WELCOME_DB_PATH
from Extensions.Utility.goodbye import DB_PATH as GOODBYE_DB_PATH
import aiosqlite

# context : this is a command which generate the server using an external api which provides the server output based on these provided instruction : @server_instruct.txt
class ConfirmView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=300)
        self.value = None
        self.template = None
        self.verification_channel = None
        self.interaction = None
        self.category_to_ignore = None
        self.is_community = None
        self.original_description = None

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

    @discord.ui.button(label="Regenerate", style=discord.ButtonStyle.blurple)
    async def regenerate(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_modal(RegenerateModal(self))

class RegenerateModal(discord.ui.Modal, title="Regenerate Template"):
    changes = discord.ui.TextInput(label="Describe your changes", style=discord.TextStyle.paragraph)

    def __init__(self, view: ConfirmView):
        super().__init__()
        self.view = view

    async def on_submit(self, interaction: discord.Interaction):
        await interaction.response.defer()
        
        # Prepare the history for regeneration
        history = [
            {"role": "user", "content": self.view.original_description},
            {"role": "assistant", "content": self.view.original_template},  # Use the original template here
            {"role": "user", "content": f"Please make the following changes to the template: {self.changes.value}"}
        ]

        print("Regeneration history:", history)  # Add this line to track history

        # Call gen_server with the updated history
        new_response = await gen_server(history)
        
        print("Regenerated response:", new_response)  # Add this line to check the response

        # Convert the new response to a dictionary
        new_template_dict = rep_to_dict(new_response)

        print("New template dict:", new_template_dict)  # Add this line to check the dictionary

        # Update the view with the new template
        self.view.template = new_template_dict

        # Show the new template
        new_embed, _ = await show_template(new_response, self.view.verification_channel)
        await interaction.followup.send("Here's the regenerated template:", embed=new_embed, view=self.view)

    def format_template_for_ai(self, template_dict):
        formatted_template = []
        for category, channels in template_dict.items():
            formatted_template.append(f"Category: {category}")
            for channel in channels:
                flags = ' '.join(f"({flag})" for flag, value in channel['flags'].items() if value)
                formatted_template.append(f"- {channel['type']}: {channel['name']} {flags}".strip())
        return '\n'.join(formatted_template)

class VerifyButton(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)  # The button doesn't timeout

    @discord.ui.button(label="Verify", style=discord.ButtonStyle.green, custom_id="verify_button")
    async def verify(self, interaction: discord.Interaction, button: discord.ui.Button):
        guild = interaction.guild
        verified_role = discord.utils.get(guild.roles, name="Verified Members")
        if not verified_role:
            return await interaction.response.send_message("Verification role not found. Please contact an administrator.", ephemeral=True)
        
        if verified_role in interaction.user.roles:
            await interaction.response.send_message("You are already verified!", ephemeral=True)
        else:
            await interaction.user.add_roles(verified_role)
            await interaction.response.send_message("You have been verified!", ephemeral=True)

def rep_to_dict(ai_response: str):
    template_dict = defaultdict(list)
    current_category = None
    channel_name_pattern = re.compile(r'"""(.*?)"""')
    flag_pattern = re.compile(r'\((.*?)\)')

    for line in ai_response.split('\n'):
        print(f"Processing line: {line}")
        line = line.strip()
        if line.startswith('**') and line.endswith('**'):
            current_category = line.strip('**')  # Remove the ** but keep the full category name
            print(f"New category found: {current_category}")
        elif (line.startswith('- Channel:') or line.startswith('- Voice:') or 
              line.startswith('- Forum:') or line.startswith('- Stage:')) and current_category:
            channel_type, channel_info = line.split(':', 1)
            channel_type = channel_type.strip('- ')
            
            # Extract channel name from triple quotes
            channel_name_match = channel_name_pattern.search(channel_info)
            if channel_name_match:
                channel_name = channel_name_match.group(1)
            else:
                channel_name = channel_info.strip()
            
            print(f"Channel found - Type: {channel_type}, Name: {channel_name}")
            
            flags = flag_pattern.findall(channel_info)
            print(f"Flags found: {flags}")
            
            flags_dict = {}
            for flag in flags:
                print(f"Processing flag: {flag}")
                if 'limit' in flag.lower():
                    limit_match = re.search(r'limit\s+(\d+)', flag, re.IGNORECASE)
                    if limit_match:
                        flags_dict['limit'] = int(limit_match.group(1))
                elif 'Post_guidelines' in flag:
                    guidelines_match = re.search(r'Post_guidelines:\s*"(.*?)"', flag)
                    if guidelines_match:
                        flags_dict['post_guidelines'] = guidelines_match.group(1)
                elif 'Tags' in flag:
                    tags_match = re.search(r'Tags:\s*\((.*?)\)', flag)
                    if tags_match:
                        flags_dict['tags'] = [tag.strip(' "') for tag in tags_match.group(1).split(',')]
                elif 'default_reaction' in flag:
                    reaction_match = re.search(r'default_reaction:\s*(.*)', flag)
                    if reaction_match:
                        flags_dict['default_reaction'] = reaction_match.group(1).strip()
                else:
                    flags_dict[flag.strip()] = True
            print(f"Processed flags: {flags_dict}")
            
            template_dict[current_category].append({
                'type': channel_type,
                'name': channel_name,
                'flags': flags_dict
            })
            print(f"Added to template_dict: {template_dict[current_category][-1]}")
    
    result = dict(template_dict)
    print(f"Final template_dict: {result}")
    return result

async def show_template(ai_response: str, verification_channel: bool):
    # Extract and format the main template structure
    template_lines = []
    current_category = None
    channel_name_pattern = re.compile(r'"""(.*?)"""')
    
    for line in ai_response.split('\n'):
        if line.startswith('**') and line.endswith('**'):
            current_category = line.strip('**')
            template_lines.append(f"<:6375moreoptions:1233770886738350103> **{current_category}**:")
        elif line.startswith('- ') and current_category:
            channel_info = line[2:].split(':', 1)
            channel_type = channel_info[0].strip()
            channel_name_info = channel_info[1].strip() if len(channel_info) > 1 else ''
            
            # Extract channel name from triple quotes
            channel_name_match = channel_name_pattern.search(channel_name_info)
            if channel_name_match:
                channel_name = channel_name_match.group(1)
            else:
                channel_name = channel_name_info
            
            emoji = "<:3280text:1233770867914440874>"
            if "Voice" in channel_type:
                emoji = "<:7032voice:1233770862633811979>"
            elif "Forum" in channel_type:
                emoji = "<:5971forum:1233770836465418291>"
            elif "Stage" in channel_type:
                emoji = "🎭"  # You can replace this with a custom stage emoji if available
            
            if "Mod_Only" in channel_name_info:
                emoji = "<:2064textlocked:1233770845634035794>" if "Voice" not in channel_type else "<:6444voicelocked:1233770856141029406>"
                emoji += " <:7715betamemberbadge:1233771451744653402>"
            elif "Private" in channel_name_info:
                emoji = "<:2064textlocked:1233770845634035794>" if "Voice" not in channel_type else "<:6444voicelocked:1233770856141029406>"
            
            template_lines.append(f"> {emoji} {channel_name}")
    
    # Join the formatted lines
    formatted_template = '\n'.join(template_lines)
    
    embed = discord.Embed(title="Server Template", description=formatted_template, color=discord.Color.blue())
    
    # Add verification system info if enabled
    if verification_channel:
        embed.add_field(name="Verification System", value="Enabled", inline=False)
    
    view = ConfirmView()  # Create a new View object
    return embed, view, formatted_template  # Return the view object instead of the formatted_template

async def delete_current_template(guild: discord.Guild, ignore_category: discord.CategoryChannel = None):
    delete_tasks = []
    for channel in guild.channels:
        if channel != guild.system_channel and (ignore_category is None or channel.category != ignore_category):
            if isinstance(channel, discord.CategoryChannel):
                if channel != ignore_category:
                    delete_tasks.append(channel.delete())
            else:
                delete_tasks.append(channel.delete())
    
    await asyncio.gather(*delete_tasks, return_exceptions=True)
    print("Finished deleting channels and categories")

async def create_channel(guild, category, channel_info, verified_role, verification_channel, is_community):
    channel_type = channel_info['type']
    channel_name = channel_info['name']
    flags = channel_info['flags']
    
    channel_kwargs = {
        'name': channel_name,
        'category': category,
    }

    if channel_type == "Voice":
        channel_kwargs['user_limit'] = flags.get('limit', 0)
        new_channel = await guild.create_voice_channel(**channel_kwargs)
    elif channel_type == "Forum" and is_community:
        tags = [discord.ForumTag(name=tag) for tag in flags.get('tags', [])]
        channel_kwargs.update({
            'topic': flags.get('post_guidelines', ''),
            'available_tags': tags[:5],  # Discord allows up to 5 tags
            'default_reaction_emoji': flags.get('default_reaction')
        })
        new_channel = await guild.create_forum(**channel_kwargs)
    elif channel_type == "Stage" and is_community:
        new_channel = await guild.create_stage_channel(**channel_kwargs)
    else:
        new_channel = await guild.create_text_channel(**channel_kwargs)

    permission_updates = []
    
    if verification_channel:
        # Set default permissions for everyone role
        permission_updates.append(new_channel.set_permissions(guild.default_role, view_channel=False))
        
        # Set permissions for verified role
        verified_perms = discord.PermissionOverwrite(view_channel=True)
        
        if flags.get('Private'):
            verified_perms.view_channel = False
        if flags.get('Read_Only'):
            verified_perms.send_messages = False
            verified_perms.add_reactions = False
            verified_perms.create_public_threads = False
        if flags.get('No_Threads'):
            verified_perms.create_public_threads = False
            verified_perms.create_private_threads = False
        if flags.get('No_Reactions'):
            verified_perms.add_reactions = False
        if flags.get('File_Upload'):
            verified_perms.attach_files = True
        
        permission_updates.append(new_channel.set_permissions(verified_role, overwrite=verified_perms))
    else:
        # If verification is disabled, use the default permission system
        if flags.get('Private'):
            permission_updates.append(new_channel.set_permissions(guild.default_role, view_channel=False))
        if flags.get('Read_Only'):
            permission_updates.append(new_channel.set_permissions(guild.default_role, send_messages=False, add_reactions=False, create_public_threads=False))
        if flags.get('No_Threads'):
            permission_updates.append(new_channel.set_permissions(guild.default_role, create_public_threads=False, create_private_threads=False))
        if flags.get('No_Reactions'):
            permission_updates.append(new_channel.set_permissions(guild.default_role, add_reactions=False))
        if flags.get('File_Upload'):
            permission_updates.append(new_channel.set_permissions(guild.default_role, attach_files=True))
    
    if flags.get('Mod_Only'):
        permission_updates.append(new_channel.set_permissions(guild.default_role, view_channel=False))
        if verified_role:
            permission_updates.append(new_channel.set_permissions(verified_role, view_channel=False))
        mod_role = discord.utils.get(guild.roles, permissions=discord.Permissions(moderate_members=True))
        if mod_role:
            permission_updates.append(new_channel.set_permissions(mod_role, view_channel=True))
    
    if flags.get('Slow_Mode'):
        permission_updates.append(new_channel.edit(slowmode_delay=30))
    
    if flags.get('NSFW'):
        permission_updates.append(new_channel.edit(nsfw=True))
    
    await asyncio.gather(*permission_updates)
    return new_channel

async def execute_template(guild: discord.Guild, template_dict: dict, verification_channel: bool, ignore_category: discord.CategoryChannel = None, is_community: bool = False, interaction: discord.Interaction = None, welcome_system: bool = False):
    print("Executing template...")
    
    verified_role = None
    if verification_channel:
        verified_role = await guild.create_role(name="Verified Members")
        print("Created 'Verified Members' role")

    # Create verification category and channel first if enabled
    if verification_channel:
        print("Setting up verification system")
        verify_category = await guild.create_category("Verification", position=0)
        verify_channel = await guild.create_text_channel("verify", category=verify_category)
        await asyncio.gather(
            verify_channel.set_permissions(guild.default_role, view_channel=True, send_messages=False, add_reactions=False, create_public_threads=False),
            verify_channel.set_permissions(verified_role, view_channel=False)
        )

        # Create a single webhook
        webhook = await verify_channel.create_webhook(name="Verification Webhook")

        # Set the webhook avatar
        avatar_url = guild.icon.url if guild.icon else (interaction.user.avatar.url if interaction and interaction.user.avatar else None)

        # Create and send the verification embed with button
        verification_embed = discord.Embed(
            title="Server Verification",
            description="Welcome to the server! To access all channels, please click the button below to verify yourself.",
            color=discord.Color.blue()
        )
        verification_embed.add_field(name="How to Verify", value="1. Click the 'Verify' button below\n2. You will receive a confirmation message\n3. Once verified, you'll have access to all channels")
        
        view = VerifyButton()
        await webhook.send(embed=verification_embed, view=view, username=guild.name, avatar_url=avatar_url)

    # Create categories and channels in batches
    category_tasks = []
    channel_tasks = []

    for position, (category_name, channels) in enumerate(template_dict.items()):
        if ignore_category and category_name == ignore_category.name:
            category = ignore_category
        else:
            category_tasks.append(guild.create_category(category_name, position=position))

    # Create all categories concurrently
    categories = await asyncio.gather(*category_tasks)

    for category, (category_name, channels) in zip(categories, template_dict.items()):
        for channel_info in channels:
            channel_tasks.append(create_channel(guild, category, channel_info, verified_role, verification_channel, is_community))

    # Create all channels concurrently
    await asyncio.gather(*channel_tasks)

    if welcome_system:
        print("Setting up welcome system")
        welcome_category = await guild.create_category("Welcome", position=1)
        welcome_channel = await guild.create_text_channel("💭︰welcome", category=welcome_category)
        goodbye_channel = await guild.create_text_channel("💭︰goodbye", category=welcome_category)

        print(f"Created welcome category: {welcome_category.name} (ID: {welcome_category.id})")
        print(f"Created welcome channel: {welcome_channel.name} (ID: {welcome_channel.id})")
        print(f"Created goodbye channel: {goodbye_channel.name} (ID: {goodbye_channel.id})")

        # Enable welcome system
        try:
            async with aiosqlite.connect(WELCOME_DB_PATH) as db:
                await db.execute("""INSERT OR REPLACE INTO welcome 
                                 (guild_id, welcome_enabled, welcome_channel) 
                                 VALUES (?, TRUE, ?)""", 
                                 (guild.id, welcome_channel.id))
                await db.commit()
            print(f"Enabled welcome system for channel: {welcome_channel.name} (ID: {welcome_channel.id})")
        except Exception as e:
            print(f"Error enabling welcome system: {str(e)}")

        # Enable goodbye system
        try:
            async with aiosqlite.connect(GOODBYE_DB_PATH) as db:
                await db.execute("""INSERT OR REPLACE INTO goodbye 
                                 (guild_id, goodbye_enabled, goodbye_channel) 
                                 VALUES (?, TRUE, ?)""", 
                                 (guild.id, goodbye_channel.id))
                await db.commit()
            print(f"Enabled goodbye system for channel: {goodbye_channel.name} (ID: {goodbye_channel.id})")
        except Exception as e:
            print(f"Error enabling goodbye system: {str(e)}")

    if verification_channel and webhook:
        # Create and send webhook embed for template application notification
        webhook_embed = discord.Embed(
            title="Server Template Applied",
            description="A new server template has been applied to this server.",
            color=discord.Color.green(), 
            timestamp=datetime.datetime.now()
        )
        webhook_embed.add_field(name="Applied by", value=interaction.user.mention if interaction else "Unknown")
        webhook_embed.set_footer(text="Server Template System | You can delete this message")
        
        await webhook.send(embed=webhook_embed, username=guild.name, avatar_url=avatar_url)

    print("Template execution complete")


async def process_template(interaction: discord.Interaction, template_dict: dict, verification_channel: bool, category_to_ignore: str = None, is_community: bool = False, welcome_system: bool = False):
    guild = interaction.guild
    if not guild:
        await interaction.followup.send("This command can only be used in a server.")
        return

    if interaction.user.id != guild.owner_id:
        await interaction.followup.send("Only the server owner can use this command.")
        return

    print("Starting template processing")
    try:
        await interaction.followup.send("Deleting current channels...")
    except discord.errors.HTTPException:
        print("Failed to send followup message. Continuing with template processing.")

    # Convert category_to_ignore from string to Category object
    ignore_category = None
    if category_to_ignore:
        ignore_category = discord.utils.get(guild.categories, id=int(category_to_ignore))
        if not ignore_category:
            await interaction.followup.send("Invalid category to ignore. Proceeding with all categories.")
            print(f"Invalid category ID: {category_to_ignore}")

    await delete_current_template(guild, ignore_category)

    try:
        await interaction.followup.send("Executing new template...")
    except discord.errors.HTTPException:
        print("Failed to send followup message. Continuing with template execution.")

    await execute_template(guild, template_dict, verification_channel, ignore_category, is_community, interaction, welcome_system)

    try:
        await interaction.followup.send("Server template has been successfully applied!")
    except discord.errors.HTTPException:
        print("Failed to send final followup message. Template processing complete.")

    print("Template processing complete")
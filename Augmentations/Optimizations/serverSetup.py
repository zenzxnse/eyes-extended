######################################################################################################################################
# <<<-------------------------------------------------------- I M P O R T S --------------------------------------------------------->>>
import discord
from discord.ext import commands
from discord import app_commands
import asyncio, os, re
from Augmentations.Ai.Gen_server import gen_server
from Augmentations.Optimizations.Execute_template import rep_to_dict, process_template
from Augmentations.Optimizations.Role_Creation import show_roles, role_rep_to_dict, execute_roles
from Augmentations.Ai.Gen_role import gen_role
from abc import ABC, abstractmethod

""" 
raw emoji data
\<:7473star:1233771382559473735> - yellow star
\<:68886roboticon:1233771391245877278> - roboticon
\<:3605twitchpartner:1233771492924457010> - violet checkmark 
\<:8355moon:1233771385839681566> - cresent moon purple
\<:7097leaveicon:1233771449227935786> - red exit
\<:3651check:1233771355451686974>- pink checkmark
 \<:9659nachessicon:1233771487102636152> - chess pawn
 \<a:fire:1235847103041900554>- flame/fire animated 
\<:3726discordlogo:1233770935971090472>- blue discord neon logo 
\<:artist_cc:1234126741593784330> - paintbrush and colors
\<:875710295253848144:1204685630534328330> - white button 
\<:875710295866216509:1204685651107254273>- red button 
\<:875710296071757824:1204685669507534858> - yellow button 
\<:7664book:1204768405513834576> - book
\<a:I_Snow_Tree:1204685956058193950>- christmas tree blurple aimated
\<a:typing:1204686985072214086> loading animated
\<a:wave_animated:1204684574802714674> - wave animated 
\<:zdeco22_cc:1223923659828236328> - click me 
\<:I_Tool:1204686012568043530> - green wrench
\<:server:1204686780775923753> - servers 
\<:t_Yes:1223251041231831174> - pink neon yes 
\<:no:1223251335839744081> - yellow neon no 
\<:Warning:1226651115181965413> - warning.
<:8355saturn:1233771388502937670> Saturn vibrant
<:73914home:1233771403845566504> home icon
<:2947joinicon:1233771444089913406> green join icon
"""


# <<<-------------------------------------------------------- E N D I M P O R T S --------------------------------------------------------->>>
######################################################################################################################################

######################################################################################################################################
# <<<-------------------------------------------------------- S E R V E R S E T U P E M B E D S --------------------------------------------------------->>>

#98b5ad
#9e98b5
#60566e
#666e56

import random

class ServerSetupEmbeds:
    colors = [0xffffda, 0x7a8067, 0xcfd2d8, 0xd9d4cc, 0x00cc99, 0x302c29, 0xffffcc, 0xb6c5f1]

    @staticmethod
    def initial_embed():
        embed = discord.Embed(
            title="<:3726discordlogo:1233770935971090472> Discord Server Setup Wizard <:3726discordlogo:1233770935971090472>",
            description="Welcome to the Discord Server Setup Wizard! This tool will guide you through creating a customized server in just a few steps.\n\n<:7473star:1233771382559473735> Let's embark on this exciting journey together! <:7473star:1233771382559473735>",
            color=random.choice(ServerSetupEmbeds.colors)
        )
        embed.add_field(name="<:7664book:1204768405513834576> Setup Process", value=
            "1. <:875710295253848144:1204685630534328330> Choose Theme Type\n"
            "2. <:875710295866216509:1204685651107254273> Select Specific Theme\n"
            "3. <:875710296071757824:1204685669507534858> Describe Your Server\n"
            "4. <:3605twitchpartner:1233771492924457010> Review Server Layout\n"
            "5. <:9659nachessicon:1233771487102636152> Select Additional Features\n"
            "6. <:3651check:1233771355451686974> Final Review and Confirmation", 
            inline=False
        )
        embed.add_field(name="<:68886roboticon:1233771391245877278> AI-Powered", value="Our advanced AI will generate a custom server layout based on your inputs!", inline=False)
        embed.add_field(name="<:8355moon:1233771385839681566> Estimated Time", value="This process typically takes 1-2 minutes to complete.", inline=False)
        embed.set_footer(text="Click 'Next' to begin the setup process • Page 1/6")
        return embed

    @staticmethod
    def theme_type_selection_embed():
        embed = discord.Embed(
            title="<:875710295253848144:1204685630534328330> Step 1: Choose Theme Type <:875710295253848144:1204685630534328330>",
            description="Select the type of theme you'd like for your server. This will determine the pool of specific themes available in the next step.",
            color=random.choice(ServerSetupEmbeds.colors)
        )
        embed.add_field(name="<:3726discordlogo:1233770935971090472> Default Themes", value="Professionally curated themes suitable for various server types.", inline=False)
        embed.add_field(name="<:artist_cc:1234126741593784330> Community Themes", value="Unique, user-created themes for more specialized server concepts.", inline=False)
        embed.add_field(name="<:I_Tool:1204686012568043530> Why This Matters", value="Your choice here will influence the overall style and structure of your server, ensuring it aligns with your vision.", inline=False)
        embed.set_footer(text="Select a theme type to continue • Page 2/6")
        return embed

    @staticmethod
    def theme_selection_embed():
        embed = discord.Embed(
            title="<:875710295866216509:1204685651107254273> Step 2: Select Specific Theme <:875710295866216509:1204685651107254273>",
            description="Now, choose a specific theme that best fits your server's purpose and style.",
            color=random.choice(ServerSetupEmbeds.colors)
        )
        embed.add_field(name="<:7473star:1233771382559473735> Theme Options", value="Each theme comes with pre-designed channels, roles, and server structure.", inline=False)
        embed.add_field(name="<:68886roboticon:1233771391245877278> AI Customization", value="Don't worry if it's not perfect - our AI will further customize it based on your description!", inline=False)
        embed.add_field(name="<:I_Tool:1204686012568043530> Tip", value="Hover over each option to see a brief description of the theme.", inline=False)
        embed.set_footer(text="Choose a theme that resonates with your vision • Page 3/6")
        return embed

    @staticmethod
    def server_description_embed():
        embed = discord.Embed(
            title="<:875710296071757824:1204685669507534858> Step 3: Describe Your Server <:875710296071757824:1204685669507534858>",
            description="Paint a vivid picture of the server you wish to create. Our AI will use this to generate a custom layout.",
            color=random.choice(ServerSetupEmbeds.colors)
        )
        embed.add_field(name="<:7664book:1204768405513834576> What to Include", value=
            "• Server purpose\n"
            "• Target audience\n"
            "• Desired atmosphere\n"
            "• Key features or activities\n"
            "• Any specific channels or roles you want", 
            inline=False
        )
        embed.add_field(name="<:68886roboticon:1233771391245877278> AI Magic", value="Our advanced AI will analyze your description and create a tailored server structure.", inline=False)
        embed.add_field(name="<:I_Tool:1204686012568043530> Tip", value="The more details you provide, the better the AI can customize your server!", inline=False)
        embed.set_footer(text="Click 'Submit' when you're done describing your server • Page 4/6")
        return embed

    @staticmethod
    def feature_selection_embed():
        embed = discord.Embed(
            title="<:9659nachessicon:1233771487102636152> Step 5: Feature Selection <:9659nachessicon:1233771487102636152>",
            description="Enhance your server with additional features. Select the ones you'd like to include.",
            color=random.choice(ServerSetupEmbeds.colors)
        )
        embed.add_field(name="<a:wave_animated:1204684574802714674> Welcome System", value=
            "Automatically greet new members with a customized message.\n"
            "• Helps newcomers feel welcomed\n"
            "• Can include server rules or guidelines\n"
            "• Customizable welcome channel", 
            inline=False
        )
        embed.add_field(name="<:3605twitchpartner:1233771492924457010> Verification System", value=
            "Add an extra layer of security to your server.\n"
            "• Prevents spam and bot accounts\n"
            "• Can include a verification process\n"
            "• Customizable verification role and channel", 
            inline=False
        )
        embed.add_field(name="<:9659nachessicon:1233771487102636152> Role Generation", value=
            "Let AI create a hierarchical role structure for your server.\n"
            "• Creates roles based on your server description\n"
            "• Includes permissions setup\n"
            "• Customizable colors and names", 
            inline=False
        )
        embed.set_footer(text="Select the features you want to include • Page 5/6")
        return embed

    @staticmethod
    def role_generation_embed():
        embed = discord.Embed(
            title="<:9659nachessicon:1233771487102636152> Role Generation <:9659nachessicon:1233771487102636152>",
            description="Let's create a custom role hierarchy for your server. Describe the roles you want, and our AI will generate them.",
            color=random.choice(ServerSetupEmbeds.colors)
        )
        embed.add_field(name="<:7664book:1204768405513834576> What to Include", value=
            "• Role names\n"
            "• Hierarchy order\n"
            "• Special permissions\n"
            "• Color preferences (if any)\n"
            "• Any unique roles specific to your server", 
            inline=False
        )
        embed.add_field(name="<:68886roboticon:1233771391245877278> AI Role Creation", value="Our AI will generate a complete role structure based on your input.", inline=False)
        embed.add_field(name="<:I_Tool:1204686012568043530> Tip", value="You'll have a chance to review and modify the roles before final confirmation.", inline=False)
        embed.set_footer(text="Describe your desired role structure • Role Generation")
        return embed

    @staticmethod
    def final_review_embed(theme_type, theme, welcome_system, verification_system, roles):
        embed = discord.Embed(
            title="<:3651check:1233771355451686974> Final Review <:3651check:1233771355451686974>",
            description="We're almost done! Let's review your server setup before we create it.",
            color=random.choice(ServerSetupEmbeds.colors)
        )
        embed.add_field(name="<:3726discordlogo:1233770935971090472> Theme Type", value=f"**{theme_type.capitalize()}**\nThis determines the overall style of your server.", inline=False)
        embed.add_field(name="<:8355moon:1233771385839681566> Specific Theme", value=f"**{theme}**\nThis provides the base structure for your server.", inline=False)
        embed.add_field(name="<a:wave_animated:1204684574802714674> Welcome System", value="**Enabled** <:t_Yes:1223251041231831174>" if welcome_system else "**Disabled** <:no:1223251335839744081>", inline=False)
        embed.add_field(name="<:3605twitchpartner:1233771492924457010> Verification System", value="**Enabled** <:t_Yes:1223251041231831174>" if verification_system else "**Disabled** <:no:1223251335839744081>", inline=False)
        embed.add_field(name="<:9659nachessicon:1233771487102636152> Custom Roles", value="**Enabled** <:t_Yes:1223251041231831174>" if roles else "**Disabled** <:no:1223251335839744081>", inline=False)
        embed.add_field(name="<:I_Tool:1204686012568043530> Next Steps", value="If everything looks good, click 'Confirm' to create your server. If you want to make changes, click 'Regenerate'.", inline=False)
        embed.set_footer(text="Review your choices and confirm to create your server • Page 6/6")
        return embed
# <<<-------------------------------------------------------- E N D S E R V E R S E T U P E M B E D S --------------------------------------------------------->>>
######################################################################################################################################

######################################################################################################################################
# <<<-------------------------------------------------------- S E R V E R S E T U P --------------------------------------------------------->>>
class ServerSetup(ABC):
    def __init__(self, bot):
        self.bot = bot
        self.default_themes = self.load_themes('DT')
        self.community_themes = self.load_themes('CT')

    def load_themes(self, folder):
        themes = {}
        path = f'Augmentations/Ai/{folder}'
        for file in os.listdir(path):
            if file.endswith('.txt'):
                themes[file[:-4]] = os.path.join(path, file)
        return themes
    
    async def show_template(self, ai_response: str, verification_channel: bool, interaction: discord.Interaction):
        # Extract and format the main template structure
        template_lines = []
        current_category = None
        channel_name_pattern = re.compile(r'"""(.*?)"""')

        for line in ai_response.split('\n'):
            line = line.strip()
            if line.startswith('Category:'):
                current_category = line[len('Category:'):].strip()
                emoji = "<:6375moreoptions:1233770886738350103>"
                template_lines.append(f"{emoji} **{current_category}**:")
            elif line.startswith('- ') and current_category:
                # Extract channel type and name
                match = re.match(r'-\s*(Channel|Voice|Forum|Stage):\s*"""(.*?)"""(?:\s*\((.*?)\))?', line)
                if match:
                    channel_type = match.group(1)
                    channel_name = match.group(2)
                    flags_str = match.group(3)

                    # Determine emoji based on channel type and flags
                    emoji = "<:3280text:1233770867914440874>"
                    if channel_type == "Voice":
                        emoji = "<:7032voice:1233770862633811979>"
                    elif channel_type == "Forum":
                        emoji = "<:5971forum:1233770836465418291>"
                    elif channel_type == "Stage":
                        emoji = "🎭"

                    # Check for specific flags that modify the emoji
                    if flags_str:
                        flags = [flag.strip() for flag in flags_str.split(',')]
                        if any('Mod_Only' in flag for flag in flags):
                            emoji = "<:2064textlocked:1233770845634035794>" if channel_type != "Voice" else "<:6444voicelocked:1233770856141029406>"
                            emoji += " <:7715betamemberbadge:1233771451744653402>"
                        elif any('Private' in flag for flag in flags):
                            emoji = "<:2064textlocked:1233770845634035794>" if channel_type != "Voice" else "<:6444voicelocked:1233770856141029406>"
                    
                    template_lines.append(f"> {emoji} {channel_name}")
            
        # Join the formatted lines
        formatted_template = '\n'.join(template_lines)
        color = random.choice(ServerSetupEmbeds.colors)
        embed = discord.Embed(
            title="**Your Server:**",
            description=f"\n{formatted_template}\n\n```yml\n---------------------------------------------```\n\n",
            color=color
        )
        embed.set_thumbnail(url=interaction.guild.icon.url if interaction.guild and interaction.guild.icon else interaction.user.display_avatar.url)
        embed.add_field(
            name="<:PinkModeratorShield:1226653308618276894> | **Parameters and their meanings**",
            value=(
                "> **(Private)** - __This channel is only visible to specific roles.__\n"
                "> **(Read_Only)** - __Members can read but not write in this channel.__\n"
                "> **(Mod_Only)** - __This channel is only visible to moderators.__\n"
                "> **(No_Threads)** - __Thread creation is disabled in this channel.__\n"
                "> **(Slow_Mode)** - __Slow mode is enabled (30 seconds delay between messages).__\n"
                "> **(NSFW)** - __This channel is marked as Not Safe For Work.__\n"
                "> **(File_Upload)** - __File uploads are allowed in this channel.__\n"
                "> **(No_Reactions)** - __Reactions are disabled in this channel.__\n"
                "> **(limit X)** - __For voice channels, sets a user limit where X is the maximum number of users.__"
            ),
            inline=True
        )

        embed.add_field(
            name="<:Warning:1226652993089441972> | **Warning**",
            value="**> __If there are any additional text in brackets following the channel names in the server structure, except for the provided parameters, or there's nothing at all then please refrain from any further actions and restart the whole process.__**",
            inline=True
        )

        embed.set_footer(
            icon_url=self.bot.user.display_avatar.url,
            text="-# This is the server structure template that will be generated. Please confirm to proceed | BY USING THIS BOT, YOU AGREE THAT WE ARE NOT LIABLE FOR ANY DATA LOSS INCURRED DURING ITS OPERATION"
        )        
        
        # Add verification system info if enabled
        if verification_channel:
            embed.add_field(name="Verification System", value="Enabled", inline=False)
        
        return embed, formatted_template

    async def theme_selection(self, interaction: discord.Interaction, theme_type):
        themes = self.community_themes if theme_type == "community" else self.default_themes
        view = ThemeSelectionView(themes, interaction)
        embed = ServerSetupEmbeds.theme_selection_embed()
        await interaction.edit_original_response(embed=embed, view=view)
        
        await view.wait()
        if view.value is None:
            await interaction.followup.send("Theme selection timed out. Please try again.")
            return None, None
        
        theme = view.value
        description = await self.server_description(interaction, theme_type, theme)
        if description is None:
            return None, None
        
        return theme, description

    async def server_description(self, interaction: discord.Interaction, theme_type, theme):
        view = ServerDescriptionView(interaction)
        embed = ServerSetupEmbeds.server_description_embed()
        await interaction.edit_original_response(embed=embed, view=view)
        
        await view.wait()
        if view.value is None:
            await interaction.followup.send("Description input timed out. Please try again.")
            return None
        
        return view.value

    async def generate_layout(self, interaction: discord.Interaction, theme_type, theme, description):
        embed = discord.Embed(title="Generating Layout", description="Please wait while we generate your server layout...", color=discord.Color.blue())
        await interaction.edit_original_response(embed=embed, view=None)
        
        theme_file = self.community_themes[theme] if theme_type == "community" else self.default_themes[theme]
        
        attempts = 0
        max_attempts = 3
        while attempts < max_attempts:
            layout = await gen_server([{"role": "user", "content": description}], instructions=theme_file)
            
            if layout is not None:
                template_dict = rep_to_dict(layout)
                if template_dict:
                    break
            
            attempts += 1
            if attempts == max_attempts:
                await interaction.followup.send("Failed to generate a valid layout after multiple attempts. Please try again.", ephemeral=True)
                await interaction.followup.send(f"Raw layout:\n```\n{layout}\n```", ephemeral=True)
                return None

        embed, formatted_template = await self.show_template(layout, False, interaction)
        server_setup_view = ServerSetupView(
            interaction,
            self.bot,
            False,  # verification_channel
            False,  # welcome_system
            None,   # category_to_ignore
            theme_type == "community",
            description,
            layout
        )
        server_setup_view.template = template_dict
        await interaction.edit_original_response(embed=embed, view=server_setup_view)

        await server_setup_view.wait()
        if server_setup_view.value is None:
            await interaction.followup.send("Layout review timed out. Please try again.")
            return None

        if not server_setup_view.value:
            await interaction.followup.send("Setup cancelled.")
            return None

        return theme_type, theme, description, template_dict

    async def feature_selection(self, interaction: discord.Interaction, theme_type, theme, description, template_dict):
        view = FeatureSelectionView(interaction)
        embed = ServerSetupEmbeds.feature_selection_embed()
        await interaction.edit_original_response(embed=embed, view=view)
        
        await view.wait()
        if view.role_generation:
            roles = await self.role_generation(interaction)
            if not roles:
                return  # User cancelled role generation
        else:
            roles = None
        
        await self.final_review(interaction, theme_type, theme, description, template_dict, view.welcome_system, view.verification_system, roles)

    async def role_generation(self, interaction: discord.Interaction):
        while True:
            view = RoleDescriptionView(interaction)
            embed = ServerSetupEmbeds.role_generation_embed()
            await interaction.edit_original_response(embed=embed, view=view)
            
            await view.wait()
            if view.value is None:
                await interaction.followup.send("Role description input timed out. Please try again.")
                return None
            
            ai_response = await gen_role([{"role": "user", "content": f"Generate roles based on this description: {view.value}"}])
            roles_dict = role_rep_to_dict(ai_response)
            
            embed, confirm_view = await show_roles(ai_response)
            confirm_view = RoleConfirmationView(interaction)
            await interaction.edit_original_response(embed=embed, view=confirm_view)
            
            await confirm_view.wait()
            if confirm_view.value is True:
                return roles_dict
            elif confirm_view.value == "regenerate":
                continue
            else:
                await interaction.followup.send("Role generation cancelled.")
                return None

    async def final_review(self, interaction: discord.Interaction, theme_type, theme, description, template_dict, welcome_system, verification_system, roles):
        embed = ServerSetupEmbeds.final_review_embed(theme_type, theme, welcome_system, verification_system, roles)
        
        view = FinalConfirmationView(interaction)
        await interaction.edit_original_response(embed=embed, view=view)
        
        await view.wait()
        if view.value is None:
            await interaction.user.send("Final confirmation timed out. Please try again.")
            return
        
        if not view.value:
            await interaction.user.send("Setup cancelled.")
            return
        
        # Create roles first
        if roles:
            try:
                await execute_roles(interaction.guild, roles)
                await interaction.user.send(f"Successfully created roles.")
            except Exception as e:
                await interaction.user.send(f"An error occurred while creating roles: {str(e)}")
                return

        # Process the server template
        try:
            await process_template(interaction, template_dict, verification_system, None, theme_type == "community", welcome_system)
            await interaction.user.send("Server setup completed successfully!")
        except Exception as e:
            await interaction.user.send(f"An error occurred while setting up the server: {str(e)}")

        # Final success message
        await interaction.user.send("Server setup process has been completed. Thank you for using the server setup command!")
# <<<-------------------------------------------------------- E N D S E R V E R S E T U P --------------------------------------------------------->>>
######################################################################################################################################

######################################################################################################################################
# <<<-------------------------------------------------------- V I E W S --------------------------------------------------------->>>



class ServerSetupView(discord.ui.View):
    def __init__(self, interaction: discord.Interaction, bot, verification_channel, welcome_system, category_to_ignore, is_community, original_description, original_template):
        super().__init__()
        self.bot = bot
        self.template = None
        self.verification_channel = verification_channel
        self.welcome_system = welcome_system
        self.category_to_ignore = category_to_ignore
        self.is_community = is_community
        self.original_description = original_description
        self.original_template = original_template
        self.value = None
        self.original_interaction = interaction

    def check_user(self, interaction: discord.Interaction) -> bool:
        return interaction.user.id == self.original_interaction.user.id

    @discord.ui.button(label="Next", style=discord.ButtonStyle.primary)
    async def next(self, interaction: discord.Interaction, button: discord.ui.Button):
        if not self.check_user(interaction):
            await interaction.response.send_message("You are not authorized to use this button.", ephemeral=True)
            return
        self.value = True
        self.stop()

    @discord.ui.button(label="Regenerate", style=discord.ButtonStyle.secondary)
    async def regenerate(self, interaction: discord.Interaction, button: discord.ui.Button):
        if not self.check_user(interaction):
            await interaction.response.send_message("You are not authorized to use this button.", ephemeral=True)
            return
        modal = RegenerateModal(self, self.bot)
        await interaction.response.send_modal(modal)

    @discord.ui.button(label="Cancel", style=discord.ButtonStyle.red)
    async def cancel(self, interaction: discord.Interaction, button: discord.ui.Button):
        if not self.check_user(interaction):
            await interaction.response.send_message("You are not authorized to use this button.", ephemeral=True)
            return
        self.value = False
        self.stop()

class RegenerateModal(discord.ui.Modal, title="Regenerate Template"):
    changes = discord.ui.TextInput(label="Describe your changes", style=discord.TextStyle.paragraph)

    def __init__(self, view: ServerSetupView, bot):
        super().__init__()
        self.view = view
        self.bot = bot

    async def on_submit(self, interaction: discord.Interaction):
        await interaction.response.defer()
        
        history = [
            {"role": "user", "content": self.view.original_description},
            {"role": "assistant", "content": self.view.original_template},
            {"role": "user", "content": f"Please make the following changes to the template: {self.changes.value}"}
        ]

        new_response = await gen_server(history)
        new_template_dict = rep_to_dict(new_response)
        self.view.template = new_template_dict
        cog = self.bot.get_cog("setup")  # Ensure this matches your cog's name

        if cog is None:
            await interaction.followup.send("ServerSetup cog is not loaded correctly.", ephemeral=True)
            return

        try:
            # Corrected unpacking: only two values expected
            new_embed, formatted_template = await cog.show_template(new_response, self.view.verification_channel, interaction)

            self.view.original_template = new_response

            await interaction.message.edit(embed=new_embed, view=self.view)
            await interaction.followup.send("Template regenerated successfully!", ephemeral=True)

        except Exception as e:
            print(f"Error in regenerating template: {e}")
            await interaction.followup.send(f"An error occurred while regenerating the template: {e}", ephemeral=True)


######################################################################################################################################
# <<<-------------------------------------------------------- T H E M E T Y P E V I E W --------------------------------------------------------->>>
class ThemeTypeView(discord.ui.View):
    def __init__(self, interaction: discord.Interaction):
        super().__init__()
        self.value = None
        self.original_interaction = interaction

    def check_user(self, interaction: discord.Interaction) -> bool:
        return interaction.user.id == self.original_interaction.user.id

    @discord.ui.button(label="Community Theme", style=discord.ButtonStyle.primary)
    async def community(self, interaction: discord.Interaction, button: discord.ui.Button):
        if not self.check_user(interaction):
            await interaction.response.send_message("You are not authorized to use this button.", ephemeral=True)
            return
        if 'COMMUNITY' not in interaction.guild.features:
            await interaction.response.send_message("This option is only available for Community-enabled servers. Please enable Community features for your server or choose the Default Theme.", ephemeral=True)
            return
        self.value = "community"
        self.stop()

    @discord.ui.button(label="Default Theme", style=discord.ButtonStyle.secondary)
    async def default(self, interaction: discord.Interaction, button: discord.ui.Button):
        if not self.check_user(interaction):
            await interaction.response.send_message("You are not authorized to use this button.", ephemeral=True)
            return
        self.value = "default"
        self.stop()
# <<<-------------------------------------------------------- E N D T H E M E T Y P E V I E W --------------------------------------------------------->>>
######################################################################################################################################

######################################################################################################################################
# <<<-------------------------------------------------------- T H E M E S E L E C T I O N V I E W --------------------------------------------------------->>>
class ThemeSelectionView(discord.ui.View):
    def __init__(self, themes, interaction: discord.Interaction):
        super().__init__()
        self.value = None
        self.original_interaction = interaction
        self.add_item(ThemeDropdown(themes, self.on_select))

    def check_user(self, interaction: discord.Interaction) -> bool:
        return interaction.user.id == self.original_interaction.user.id

    async def on_select(self, interaction: discord.Interaction, value):
        if not self.check_user(interaction):
            await interaction.response.send_message("You are not authorized to use this dropdown.", ephemeral=True)
            return
        self.value = value
        await interaction.response.defer()
        self.stop()
# <<<-------------------------------------------------------- E N D T H E M E S E L E C T I O N V I E W --------------------------------------------------------->>>
######################################################################################################################################

######################################################################################################################################
# <<<-------------------------------------------------------- T H E M E D R O P D O W N --------------------------------------------------------->>>
class ThemeDropdown(discord.ui.Select):
    def __init__(self, themes, callback):
        options = [discord.SelectOption(label=theme, value=theme) for theme in themes]
        super().__init__(placeholder="Choose a theme...", min_values=1, max_values=1, options=options)
        self.callback_func = callback

    async def callback(self, interaction: discord.Interaction):
        await self.callback_func(interaction, self.values[0])
# <<<-------------------------------------------------------- E N D T H E M E D R O P D O W N --------------------------------------------------------->>>
######################################################################################################################################

######################################################################################################################################
# <<<-------------------------------------------------------- S E R V E R D E S C R I P T I O N V I E W --------------------------------------------------------->>>
class ServerDescriptionView(discord.ui.View):
    def __init__(self, interaction: discord.Interaction):
        super().__init__()
        self.value = None
        self.original_interaction = interaction

    def check_user(self, interaction: discord.Interaction) -> bool:
        return interaction.user.id == self.original_interaction.user.id

    @discord.ui.button(label="Describe Server", style=discord.ButtonStyle.primary)
    async def describe(self, interaction: discord.Interaction, button: discord.ui.Button):
        if not self.check_user(interaction):
            await interaction.response.send_message("You are not authorized to use this button.", ephemeral=True)
            return
        modal = ServerDescriptionModal()
        await interaction.response.send_modal(modal)
        self.value = await modal.wait()
        self.stop()
# <<<-------------------------------------------------------- E N D S E R V E R D E S C R I P T I O N V I E W --------------------------------------------------------->>>
######################################################################################################################################

######################################################################################################################################
# <<<-------------------------------------------------------- S E R V E R D E S C R I P T I O N M O D A L --------------------------------------------------------->>>
class ServerDescriptionModal(discord.ui.Modal, title="Describe Your Server"):
    description = discord.ui.TextInput(label="Server Description", style=discord.TextStyle.paragraph)

    async def on_submit(self, interaction: discord.Interaction):
        await interaction.response.defer()
        self.interaction = interaction

    async def wait(self):
        await super().wait()
        return self.description.value
# <<<-------------------------------------------------------- E N D S E R V E R D E S C R I P T I O N M O D A L --------------------------------------------------------->>>
######################################################################################################################################

######################################################################################################################################
# <<<-------------------------------------------------------- F E A T U R E S E L E C T I O N V I E W --------------------------------------------------------->>>
class FeatureSelectionView(discord.ui.View):
    def __init__(self, interaction: discord.Interaction):
        super().__init__()
        self.welcome_system = False
        self.verification_system = False
        self.role_generation = False
        self.interaction = None
        self.original_interaction = interaction

    def check_user(self, interaction: discord.Interaction) -> bool:
        return interaction.user.id == self.original_interaction.user.id

    @discord.ui.select(placeholder="Select additional features...", min_values=0, max_values=3, options=[
        discord.SelectOption(label="Welcome System", value="welcome"),
        discord.SelectOption(label="Verification System", value="verification"),
        discord.SelectOption(label="Role Generation", value="roles")
    ])
    async def select_features(self, interaction: discord.Interaction, select: discord.ui.Select):
        if not self.check_user(interaction):
            await interaction.response.send_message("You are not authorized to use this dropdown.", ephemeral=True)
            return
        self.welcome_system = "welcome" in select.values
        self.verification_system = "verification" in select.values
        self.role_generation = "roles" in select.values
        await interaction.response.defer()

    @discord.ui.button(label="Confirm", style=discord.ButtonStyle.primary)
    async def confirm(self, interaction: discord.Interaction, button: discord.ui.Button):
        if not self.check_user(interaction):
            await interaction.response.send_message("You are not authorized to use this button.", ephemeral=True)
            return
        self.interaction = interaction
        self.stop()
# <<<-------------------------------------------------------- E N D F E A T U R E S E L E C T I O N V I E W --------------------------------------------------------->>>
######################################################################################################################################

######################################################################################################################################
# <<<-------------------------------------------------------- F I N A L C O N F I R M A T I O N V I E W --------------------------------------------------------->>>
class FinalConfirmationView(discord.ui.View):
    def __init__(self, interaction: discord.Interaction):
        super().__init__()
        self.value = None
        self.original_interaction = interaction

    def check_user(self, interaction: discord.Interaction) -> bool:
        return interaction.user.id == self.original_interaction.user.id

    @discord.ui.button(label="Confirm", style=discord.ButtonStyle.green)
    async def confirm(self, interaction: discord.Interaction, button: discord.ui.Button):
        if not self.check_user(interaction):
            await interaction.response.send_message("You are not authorized to use this button.", ephemeral=True)
            return
        self.value = True
        self.stop()

    @discord.ui.button(label="Cancel", style=discord.ButtonStyle.red)
    async def cancel(self, interaction: discord.Interaction, button: discord.ui.Button):
        if not self.check_user(interaction):
            await interaction.response.send_message("You are not authorized to use this button.", ephemeral=True)
            return
        self.value = False
        self.stop()
# <<<-------------------------------------------------------- E N D F I N A L C O N F I R M A T I O N V I E W --------------------------------------------------------->>>
######################################################################################################################################

######################################################################################################################################
# <<<-------------------------------------------------------- R O L E D E S C R I P T I O N V I E W --------------------------------------------------------->>>
class RoleDescriptionView(discord.ui.View):
    def __init__(self, interaction: discord.Interaction):
        super().__init__()
        self.value = None
        self.original_interaction = interaction

    def check_user(self, interaction: discord.Interaction) -> bool:
        return interaction.user.id == self.original_interaction.user.id

    @discord.ui.button(label="Describe Roles", style=discord.ButtonStyle.primary)
    async def describe(self, interaction: discord.Interaction, button: discord.ui.Button):
        if not self.check_user(interaction):
            await interaction.response.send_message("You are not authorized to use this button.", ephemeral=True)
            return
        modal = RoleDescriptionModal()
        await interaction.response.send_modal(modal)
        self.value = await modal.wait()
        self.stop()
# <<<-------------------------------------------------------- E N D R O L E D E S C R I P T I O N V I E W --------------------------------------------------------->>>
######################################################################################################################################

######################################################################################################################################
# <<<-------------------------------------------------------- R O L E D E S C R I P T I O N M O D A L --------------------------------------------------------->>>
class RoleDescriptionModal(discord.ui.Modal, title="Describe Your Server Roles"):
    description = discord.ui.TextInput(label="Role Description", style=discord.TextStyle.paragraph)

    async def on_submit(self, interaction: discord.Interaction):
        await interaction.response.defer()
        self.interaction = interaction

    async def wait(self):
        await super().wait()
        return self.description.value
# <<<-------------------------------------------------------- E N D R O L E D E S C R I P T I O N M O D A L --------------------------------------------------------->>>
######################################################################################################################################

######################################################################################################################################
# <<<-------------------------------------------------------- R O L E C O N F I R M A T I O N V I E W --------------------------------------------------------->>>
class RoleConfirmationView(discord.ui.View):
    def __init__(self, interaction: discord.Interaction):
        super().__init__()
        self.value = None
        self.original_interaction = interaction

    def check_user(self, interaction: discord.Interaction) -> bool:
        return interaction.user.id == self.original_interaction.user.id

    @discord.ui.button(label="Confirm", style=discord.ButtonStyle.green)
    async def confirm(self, interaction: discord.Interaction, button: discord.ui.Button):
        if not self.check_user(interaction):
            await interaction.response.send_message("You are not authorized to use this button.", ephemeral=True)
            return
        await interaction.response.defer()
        self.value = True
        self.stop()

    @discord.ui.button(label="Regenerate", style=discord.ButtonStyle.primary)
    async def regenerate(self, interaction: discord.Interaction, button: discord.ui.Button):
        if not self.check_user(interaction):
            await interaction.response.send_message("You are not authorized to use this button.", ephemeral=True)
            return
        await interaction.response.defer()
        self.value = "regenerate"
        self.stop()

    @discord.ui.button(label="Cancel", style=discord.ButtonStyle.red)
    async def cancel(self, interaction: discord.Interaction, button: discord.ui.Button):
        if not self.check_user(interaction):
            await interaction.response.send_message("You are not authorized to use this button.", ephemeral=True)
            return
        await interaction.response.defer()
        self.value = False
        self.stop()
# <<<-------------------------------------------------------- E N D R O L E C O N F I R M A T I O N V I E W --------------------------------------------------------->>>
######################################################################################################################################

# <<<-------------------------------------------------------- E N D V I E W S --------------------------------------------------------->>>
######################################################################################################################################

async def setup(bot):
    await bot.add_cog(ServerSetup(bot))

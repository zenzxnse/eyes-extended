import discord
from discord.ext import commands
from typing import List
import asyncio
import random

# Define the list of colors to choose from
colors = [
    0x1ABC9C,  # Turquoise
    0x3498DB,  # Blue
    0x9B59B6,  # Purple
    0xE74C3C,  # Red
    0xF1C40F,  # Yellow
    0x2ECC71,  # Green
    0xE67E22,  # Orange
    0x95A5A6,  # Grey
    0x34495E,  # Dark Blue
    0x16A085   # Dark Turquoise
]

class EmbedManualView(discord.ui.View):
    def __init__(self, pages: List[discord.Embed], timeout: float = 300.0):
        super().__init__(timeout=timeout)
        self.pages = pages
        self.current_page = 0
        self.update_buttons()

    def update_buttons(self):
        # Clear existing buttons to update their states
        self.clear_items()
        # Previous Page Button
        prev_emoji = "⬅️"  
        self.add_item(PreviousPageButton(emoji=prev_emoji))
        # Home Button
        home_emoji = "🏠" 
        self.add_item(HomeButton(emoji=home_emoji))
        # Next Page Button
        next_emoji = "➡️"  # Green join icon
        self.add_item(NextPageButton(emoji=next_emoji))

    async def on_timeout(self):
        # Disable all buttons when timeout occurs
        for item in self.children:
            item.disabled = True
        # Edit the message to disable buttons
        # Note: This requires the original message reference, which isn't stored here.
        # To implement this, you might need to override the interaction response or store the message.
        pass

    async def change_page(self, interaction: discord.Interaction, new_page: int):
        self.current_page = new_page
        await interaction.response.edit_message(embed=self.pages[self.current_page], view=self)
        self.update_buttons()

class PreviousPageButton(discord.ui.Button):
    def __init__(self, emoji: str):
        super().__init__(style=discord.ButtonStyle.primary, emoji=emoji)

    async def callback(self, interaction: discord.Interaction):
        view: EmbedManualView = self.view
        if view.current_page > 0:
            view.current_page -= 1
            await interaction.response.edit_message(embed=view.pages[view.current_page], view=view)
        else:
            await interaction.response.send_message("You are already on the first page.", ephemeral=True)

class NextPageButton(discord.ui.Button):
    def __init__(self, emoji: str):
        super().__init__(style=discord.ButtonStyle.primary, emoji=emoji)

    async def callback(self, interaction: discord.Interaction):
        view: EmbedManualView = self.view
        if view.current_page < len(view.pages) - 1:
            view.current_page += 1
            await interaction.response.edit_message(embed=view.pages[view.current_page], view=view)
        else:
            await interaction.response.send_message("You are already on the last page.", ephemeral=True)

class HomeButton(discord.ui.Button):
    def __init__(self, emoji: str):
        super().__init__(style=discord.ButtonStyle.success, emoji=emoji)

    async def callback(self, interaction: discord.Interaction):
        view: EmbedManualView = self.view
        view.current_page = 0
        await interaction.response.edit_message(embed=view.pages[view.current_page], view=view)

class EmbedPages:
    def __init__(self, bot):
        self.bot = bot
        self.pages = self.create_pages()

    def create_pages(self) -> List[discord.Embed]:
        pages = []

        # Page 1: Introduction
        embed = discord.Embed(
            title="<:7473star:1233771382559473735> **Embed Creation Guide: Introduction**",
            description=(
                "Welcome to the comprehensive guide on creating and managing embeds with **O' bot**! 🌟\n\n"
                "**Embeds** are powerful tools in Discord that allow you to present information in a structured and visually appealing way. This guide will walk you through every feature of the embed system, including manual creation and AI-powered generation."
            ),
            color=random.choice(colors)
        )
        embed.add_field(
            name="__What are Embeds?__",
            value=(
                "Embeds are rich content blocks that can contain formatted text, images, links, and more. They help in organizing information neatly and enhancing the visual appeal of your messages."
            ),
            inline=False
        )
        embed.add_field(
            name="__Navigation__",
            value=(
                "Use the ⬅️ and ➡️ buttons to navigate through the pages. The 🏠 button will bring you back to this introduction."
            ),
            inline=False
        )
        embed.set_footer(
            text="-# Navigation - Use the ⬅️ and ➡️ buttons to navigate through the pages. The 🏠 button will bring you back to this introduction."
        )
        embed.set_author(
            name="Page 1 | Introduction",
            icon_url=self.bot.user.avatar.url if self.bot.user.avatar else discord.Embed.Empty
        )
        pages.append(embed)

        # Page 2: Embed Builder Overview
        embed = discord.Embed(
            title="<:68886roboticon:1233771391245877278> **Embed Builder Overview**",
            description=(
                "The **Embed Builder** is an intuitive tool that allows you to create embeds without diving into complex commands. It's perfect for users who prefer a guided experience."
            ),
            color=random.choice(colors)
        )
        embed.add_field(
            name="__How to Access__",
            value="Use the `/embed builder` command to start the Embed Builder.",
            inline=False
        )
        embed.add_field(
            name="__Features__",
            value=(
                "**•** Add title, description, and fields\n"
                "**•** Set embed color\n"
                "**•** Add images and thumbnails\n"
                "**•** Create buttons easily"
            ),
            inline=False
        )
        embed.add_field(
            name="__Saving Embeds__",
            value=(
                "The Embed Builder allows you to save your creations with a custom name for easy recall later. This helps in organizing your embeds and reusing them whenever needed."
            ),
            inline=False
        )
        embed.set_footer(
            text="-# Navigation - Use the ⬅️ and ➡️ buttons to navigate through the pages. The 🏠 button will bring you back to this introduction."
        )
        embed.set_author(
            name="Page 2 | Embed Builder Overview",
            icon_url=self.bot.user.avatar.url if self.bot.user.avatar else discord.Embed.Empty
        )
        pages.append(embed)

        # Page 3: Creating an Embed with Embed Builder
        embed = discord.Embed(
            title="<:3605twitchpartner:1233771492924457010> **Creating an Embed with Embed Builder**",
            description=(
                "Follow this step-by-step guide to create your first embed using the Embed Builder."
            ),
            color=random.choice(colors)
        )
        embed.add_field(
            name="__Step 1: Start the Builder__",
            value="Use the `/embed builder` command to initiate the Embed Builder.",
            inline=False
        )
        embed.add_field(
            name="__Step 2: Add Content__",
            value=(
                "Follow the prompts to add:\n"
                "**•** *Title*: The main heading of your embed.\n"
                "**•** *Description*: Detailed information or message.\n"
                "**•** *Fields*: Additional information organized neatly.\n"
                "**•** *Color*: Choose a color that represents your theme."
            ),
            inline=False
        )
        embed.add_field(
            name="__Step 3: Add Media__",
            value=(
                "Enhance your embed with visuals:\n"
                "**•** *Thumbnail Image*: A small image displayed on the side.\n"
                "**•** *Main Image*: A larger image that takes center stage."
            ),
            inline=False
        )
        embed.add_field(
            name="__Step 4: Preview and Save__",
            value=(
                "Review your embed to ensure everything looks perfect. Once satisfied, save it with a unique name for future use."
            ),
            inline=False
        )
        embed.set_footer(
            text="-# Navigation - Use the ⬅️ and ➡️ buttons to navigate through the pages. The 🏠 button will bring you back to this introduction."
        )
        embed.set_author(
            name="Page 3 | Creating an Embed with Embed Builder",
            icon_url=self.bot.user.avatar.url if self.bot.user.avatar else discord.Embed.Empty
        )
        pages.append(embed)

        # Page 4: Adding Buttons with Embed Builder
        embed = discord.Embed(
            title="<:8355moon:1233771385839681566> **Adding Buttons with Embed Builder**",
            description=(
                "Interactive buttons can make your embeds more engaging. Learn how to add them effortlessly."
            ),
            color=random.choice(colors)
        )
        embed.add_field(
            name="__Button Types__",
            value=(
                "**• URL Buttons**: Link to external websites or resources.\n"
                "**• Custom ID Buttons**: Trigger specific bot actions or commands."
            ),
            inline=False
        )
        embed.add_field(
            name="__Adding a Button__",
            value=(
                "1. Choose **'Add Button'** in the builder.\n"
                "2. Select the button type you want to add.\n"
                "3. Set the **label** and **URL/Custom ID** based on the button type.\n"
                "4. Choose a **button color** to match your embed's theme."
            ),
            inline=False
        )
        embed.add_field(
            name="__Button Limits__",
            value="You can add up to **5 buttons** per embed action row to maintain clarity and usability.",
            inline=False
        )
        embed.set_footer(
            text="-# Navigation - Use the ⬅️ and ➡️ buttons to navigate through the pages. The 🏠 button will bring you back to this introduction."
        )
        embed.set_author(
            name="Page 4 | Adding Buttons with Embed Builder",
            icon_url=self.bot.user.avatar.url if self.bot.user.avatar else discord.Embed.Empty
        )
        pages.append(embed)

        # Page 5: Manual Embed Creation
        embed = discord.Embed(
            title="<:7097leaveicon:1233771449227935786> **Manual Embed Creation**",
            description=(
                "For users who prefer granular control, manual embed creation offers flexibility and precision."
            ),
            color=random.choice(colors)
        )
        embed.add_field(
            name="__Basic Command__",
            value="```/embed create <name> <title> <description>```",
            inline=False
        )
        embed.add_field(
            name="__Adding Fields__",
            value="```/embed field add <embed_name> <field_name> <field_value> [inline]```",
            inline=False
        )
        embed.add_field(
            name="__Setting Color__",
            value="```/embed color <embed_name> <color_hex>```",
            inline=False
        )
        embed.add_field(
            name="__Adding Images__",
            value=(
                "```/embed image <embed_name> <image_url>\n"
                "/embed thumbnail <embed_name> <thumbnail_url>```"
            ),
            inline=False
        )
        embed.set_footer(
            text="-# Navigation - Use the ⬅️ and ➡️ buttons to navigate through the pages. The 🏠 button will bring you back to this introduction."
        )
        embed.set_author(
            name="Page 5 | Manual Embed Creation",
            icon_url=self.bot.user.avatar.url if self.bot.user.avatar else discord.Embed.Empty
        )
        pages.append(embed)

        # Page 6: Managing Saved Embeds
        embed = discord.Embed(
            title="<:3651check:1233771355451686974> **Managing Saved Embeds**",
            description=(
                "Efficiently manage your saved embeds by viewing, editing, and organizing them with ease."
            ),
            color=random.choice(colors)
        )
        embed.add_field(
            name="__Listing Embeds__",
            value="```/embed list``` - Displays a list of all your saved embeds.",
            inline=False
        )
        embed.add_field(
            name="__Viewing an Embed__",
            value="```/embed show <embed_name>``` - Displays the specified embed.",
            inline=False
        )
        embed.add_field(
            name="__Editing an Embed__",
            value=(
                "Use the same creation commands with an existing embed name to modify its properties.\n"
                "For example:\n```/embed title <embed_name> <new_title>```"
            ),
            inline=False
        )
        embed.add_field(
            name="__Deleting an Embed__",
            value="```/embed delete <embed_name>``` - Removes the specified embed from your saved list.",
            inline=False
        )
        embed.set_footer(
            text="-# Navigation - Use the ⬅️ and ➡️ buttons to navigate through the pages. The 🏠 button will bring you back to this introduction."
        )
        embed.set_author(
            name="Page 6 | Managing Saved Embeds",
            icon_url=self.bot.user.avatar.url if self.bot.user.avatar else discord.Embed.Empty
        )
        pages.append(embed)

        # Page 7: AI Embed Generation
        embed = discord.Embed(
            title="<:9659nachessicon:1233771487102636152> **AI Embed Generation**",
            description=(
                "Leverage the power of AI to generate beautiful and customized embeds automatically!"
            ),
            color=random.choice(colors)
        )
        embed.add_field(
            name="__How It Works__",
            value=(
                "Our AI analyzes your description and generates an embed that matches your specifications, including title, description, color, images, and more."
            ),
            inline=False
        )
        embed.add_field(
            name="__Using AI Generation__",
            value="```/ai embed generate <description>``` - Generates an embed based on your provided description.",
            inline=False
        )
        embed.add_field(
            name="__Tips for Good Results__",
            value=(
                "**•** *Be specific* in your description.\n"
                "**•** Mention desired *colors*, *themes*, or *moods*.\n"
                "**•** Specify if you want *fields* or *images*."
            ),
            inline=False
        )
        embed.add_field(
            name="__Editing AI-Generated Embeds__",
            value=(
                "You can further customize AI-generated embeds using the standard embed editing commands.\n"
                "For example:\n```/embed color <embed_name> <new_color_hex>```"
            ),
            inline=False
        )
        embed.set_footer(
            text="-# Navigation - Use the ⬅️ and ➡️ buttons to navigate through the pages. The 🏠 button will bring you back to this introduction."
        )
        embed.set_author(
            name="Page 7 | AI Embed Generation",
            icon_url=self.bot.user.avatar.url if self.bot.user.avatar else discord.Embed.Empty
        )
        pages.append(embed)

        # Page 8: Advanced Button Features
        embed = discord.Embed(
            title="<a:fire:1235847103041900554> **Advanced Button Features**",
            description=(
                "Enhance your embeds with advanced button functionalities to create interactive experiences."
            ),
            color=random.choice(colors)
        )
        embed.add_field(
            name="__Manual Button Addition__",
            value="```/embed button add <embed_name> <label> <style> <custom_id_or_url>``` - Adds a button to the specified embed.",
            inline=False
        )
        embed.add_field(
            name="__Button Styles__",
            value=(
                "**• Primary (Blurple)**: Default button.\n"
                "**• Secondary (Grey)**: Alternative actions.\n"
                "**• Success (Green)**: Indicates a positive action.\n"
                "**• Danger (Red)**: Indicates caution or destructive action.\n"
                "**• Link**: Directs to an external URL."
            ),
            inline=False
        )
        embed.add_field(
            name="__Custom ID Buttons__",
            value=(
                "These buttons can trigger specific bot actions. Collaborate with your bot developer to implement custom behaviors and functionalities."
            ),
            inline=False
        )
        embed.add_field(
            name="__Removing Buttons__",
            value="```/embed button remove <embed_name> <button_index>``` - Removes a button from the specified embed based on its index.",
            inline=False
        )
        embed.set_footer(
            text="-# Navigation - Use the ⬅️ and ➡️ buttons to navigate through the pages. The 🏠 button will bring you back to this introduction."
        )
        embed.set_author(
            name="Page 8 | Advanced Button Features",
            icon_url=self.bot.user.avatar.url if self.bot.user.avatar else discord.Embed.Empty
        )
        pages.append(embed)

        # Page 9: Embed Quotas and Limitations
        embed = discord.Embed(
            title="<:3726discordlogo:1233770935971090472> **Embed Quotas and Limitations**",
            description=(
                "Understanding the boundaries of embed creation and storage ensures optimal performance and organization."
            ),
            color=random.choice(colors)
        )
        embed.add_field(
            name="__User Quota__",
            value="Each user can save up to **25 embeds**. Plan and organize your embeds to make the most out of your quota.",
            inline=False
        )
        embed.add_field(
            name="__Embed Size Limits__",
            value=(
                "**• Title**: 256 characters\n"
                "**• Description**: 4096 characters\n"
                "**• Field Name**: 256 characters\n"
                "**• Field Value**: 1024 characters\n"
                "**• Footer**: 2048 characters\n"
                "**• Author Name**: 256 characters"
            ),
            inline=False
        )
        embed.add_field(
            name="__Other Limitations__",
            value=(
                "**• Max 25 fields per embed**\n"
                "**• Max 5 buttons per action row**\n"
                "**• Max 5 action rows per message**"
            ),
            inline=False
        )
        embed.set_footer(
            text="-# Navigation - Use the ⬅️ and ➡️ buttons to navigate through the pages. The 🏠 button will bring you back to this introduction."
        )
        embed.set_author(
            name="Page 9 | Embed Quotas and Limitations",
            icon_url=self.bot.user.avatar.url if self.bot.user.avatar else discord.Embed.Empty
        )
        pages.append(embed)

        # Page 10: Best Practices and Tips
        embed = discord.Embed(
            title="<:artist_cc:1234126741593784330> **Best Practices and Tips**",
            description=(
                "Enhance your embeds with these best practices to make them more effective and visually appealing."
            ),
            color=random.choice(colors)
        )
        embed.add_field(
            name="__Design Tips__",
            value=(
                "**•** *Use consistent colors* for a cohesive look.\n"
                "**•** Utilize **markdown** for text formatting to highlight important sections.\n"
                "**•** Keep titles *concise and descriptive* to immediately convey the embed's purpose."
            ),
            inline=False
        )
        embed.add_field(
            name="__Content Organization__",
            value=(
                "**•** Use **fields** to break up long content into manageable sections.\n"
                "**•** Place the most important information at the top to grab attention.\n"
                "**•** Use **thumbnails** to add visual interest and support the embed's content."
            ),
            inline=False
        )
        embed.add_field(
            name="__Interaction Design__",
            value=(
                "**•** Use **buttons** for clear call-to-actions, guiding users on what to do next.\n"
                "**•** Limit the number of buttons to avoid overwhelming users; aim for clarity.\n"
                "**•** Ensure **button labels** are clear and action-oriented, making their purpose obvious."
            ),
            inline=False
        )
        embed.add_field(
            name="__Testing__",
            value=(
                "Always **preview your embeds** before saving or sending them to ensure they look and function as intended. Testing helps in identifying and rectifying any issues early on."
            ),
            inline=False
        )
        embed.set_footer(
            text="-# Navigation - Use the ⬅️ and ➡️ buttons to navigate through the pages. The 🏠 button will bring you back to this introduction."
        )
        embed.set_author(
            name="Page 10 | Best Practices and Tips",
            icon_url=self.bot.user.avatar.url if self.bot.user.avatar else discord.Embed.Empty
        )
        pages.append(embed)

        # Additional Pages: Detailed Code Explanations

        # Page 11: Understanding embed.py
        embed = discord.Embed(
            title="<:7664book:1204768405513834576> **Understanding embed.py**",
            description=(
                "Dive into the `embed.py` file to understand how embeds are structured and managed within the bot."
            ),
            color=random.choice(colors)
        )
        embed.add_field(
            name="__File Path__",
            value="`Extensions/Utility/embed.py`",
            inline=False
        )
        embed.add_field(
            name="__Key Classes and Methods__",
            value=(
                "**•** `EmbedProject` Class: Handles embed creation, storage, retrieval, and deletion.\n"
                "**•** `save_user_embeds` Method: Saves a new embed to the user's collection.\n"
                "**•** `get_user_embeds` Method: Retrieves all embeds saved by a user.\n"
                "**•** `embed_exists` Method: Checks if an embed with a given name already exists.\n"
                "**•** `add_field_to_embed` Method: Adds a field to an existing embed.\n"
                "**•** `retrieve_embed_data` Method: Fetches detailed data of a specific embed."
            ),
            inline=False
        )
        embed.add_field(
            name="__Workflow Overview__",
            value=(
                "1. **Creation**: Users can create embeds either manually or using the Embed Builder.\n"
                "2. **Storage**: Embeds are saved in a structured format, allowing easy retrieval and management.\n"
                "3. **Retrieval**: Users can list, view, edit, or delete their saved embeds as needed."
            ),
            inline=False
        )
        embed.add_field(
            name="__Integration Points__",
            value=(
                "The `embed.py` utilities are leveraged by various cogs and commands within the bot, ensuring consistency and reliability in embed management."
            ),
            inline=False
        )
        embed.set_footer(
            text="-# Navigation - Use the ⬅️ and ➡️ buttons to navigate through the pages. The 🏠 button will bring you back to this introduction."
        )
        embed.set_author(
            name="Page 11 | Understanding embed.py",
            icon_url=self.bot.user.avatar.url if self.bot.user.avatar else discord.Embed.Empty
        )
        pages.append(embed)

        # Page 12: Exploring AI Embed Generation (ai_embed_gen.py)
        embed = discord.Embed(
            title="<:I_Tool:1204686012568043530> **Exploring AI Embed Generation (ai_embed_gen.py)**",
            description=(
                "Understand how AI is utilized to automate and enhance embed creation within the bot."
            ),
            color=random.choice(colors)
        )
        embed.add_field(
            name="__File Path__",
            value="`Extensions/AI/ai_embed_gen.py`",
            inline=False
        )
        embed.add_field(
            name="__Key Classes and Methods__",
            value=(
                "**•** `AI_Embed_Gen` Class: A `commands.GroupCog` that handles AI-powered embed generation.\n"
                "**•** `aiEmbedGenerate` Method: Command to generate an embed based on user-provided description.\n"
                "**•** `extract_embed_data` Method: Parses AI responses to extract embed properties using regex."
            ),
            inline=False
        )
        embed.add_field(
            name="__AI Integration__",
            value=(
                "The `AI_Embed_Gen` cog interacts with AI augmentation tools to interpret user descriptions and generate structured embed data. This seamless integration allows users to create complex embeds effortlessly."
            ),
            inline=False
        )
        embed.add_field(
            name="__Error Handling__",
            value=(
                "Robust error handling ensures that users receive clear feedback in case of issues during embed generation, such as exceeding quota limits or invalid input formats."
            ),
            inline=False
        )
        embed.set_footer(
            text="-# Navigation - Use the ⬅️ and ➡️ buttons to navigate through the pages. The 🏠 button will bring you back to this introduction."
        )
        embed.set_author(
            name="Page 12 | Exploring AI Embed Generation (ai_embed_gen.py)",
            icon_url=self.bot.user.avatar.url if self.bot.user.avatar else discord.Embed.Empty
        )
        pages.append(embed)

        # Page 13: Creating Interactive Buttons
        embed = discord.Embed(
            title="<:I_Tool:1204686012568043530> **Creating Interactive Buttons**",
            description=(
                "Enhance your embeds with interactive buttons to engage users and trigger specific actions."
            ),
            color=random.choice(colors)
        )
        embed.add_field(
            name="__Button Components__",
            value=(
                "**•** *Label*: The text displayed on the button.\n"
                "**•** *Style*: Determines the button's color and behavior (e.g., Primary, Secondary, Success).\n"
                "**•** *Custom ID/URL*: Defines the action triggered when the button is clicked."
            ),
            inline=False
        )
        embed.add_field(
            name="__Adding Buttons in Embed Builder__",
            value=(
                "1. Select the **'Add Button'** option in the Embed Builder.\n"
                "2. Choose between **URL** or **Custom ID** button types.\n"
                "3. Define the **label** and corresponding **URL/Custom ID**.\n"
                "4. Pick a **button style** that aligns with your embed's theme."
            ),
            inline=False
        )
        embed.add_field(
            name="__Manual Button Creation__",
            value=(
                "For more control, manually add buttons using commands:\n"
                "**Example:**\n```/embed button add WelcomeEmbed 'Click Me' primary https://example.com```"
            ),
            inline=False
        )
        embed.add_field(
            name="__Button Limits__",
            value="Maintain usability by limiting to **5 buttons per action row** and ensuring button labels are clear and concise.",
            inline=False
        )
        embed.set_footer(
            text="-# Navigation - Use the ⬅️ and ➡️ buttons to navigate through the pages. The 🏠 button will bring you back to this introduction."
        )
        embed.set_author(
            name="Page 13 | Creating Interactive Buttons",
            icon_url=self.bot.user.avatar.url if self.bot.user.avatar else discord.Embed.Empty
        )
        pages.append(embed)

        # Page 14: Navigating the Embed Manual
        embed = discord.Embed(
            title="<:I_Tool:1204686012568043530> **Navigating the Embed Manual**",
            description=(
                "Master the navigation of this manual to quickly find the information you need."
            ),
            color=random.choice(colors)
        )
        embed.add_field(
            name="__Buttons Overview__",
            value=(
                "**• Previous Page** (Home Icon): Takes you to the previous page.\n"
                "**• Home** (Wave Animated): Returns you to the Introduction page.\n"
                "**• Next Page** (Join Icon): Takes you to the next page."
            ),
            inline=False
        )
        embed.add_field(
            name="__Page Indicators__",
            value="Each page is clearly labeled in the footer for easy reference.",
            inline=False
        )
        embed.add_field(
            name="__Timeout Behavior__",
            value=(
                "The manual will automatically disable navigation buttons after **5 minutes** of inactivity to prevent clutter."
            ),
            inline=False
        )
        embed.add_field(
            name="__Accessibility__",
            value=(
                "Use keyboard shortcuts and Discord's built-in accessibility features alongside this manual for an inclusive experience."
            ),
            inline=False
        )
        embed.set_footer(
            text="-# Navigation - Use the Previous, Home, and Next buttons to traverse through the manual. Buttons will disable after inactivity."
        )
        embed.set_author(
            name="Page 14 | Navigating the Embed Manual",
            icon_url=self.bot.user.avatar.url if self.bot.user.avatar else discord.Embed.Empty
        )
        pages.append(embed)

        # Page 15: Troubleshooting Common Issues
        embed = discord.Embed(
            title="<:Warning:1226651115181965413> **Troubleshooting Common Issues**",
            description=(
                "Encountering problems? Here's how to resolve some of the most common issues with embed creation and management."
            ),
            color=random.choice(colors)
        )
        embed.add_field(
            name="__Exceeded Embed Quota__",
            value=(
                "If you receive a message indicating you've reached the maximum limit of **25 embeds**, delete some unused embeds using the `*delete <embed name>` command or view your embeds with `/embed list`."
            ),
            inline=False
        )
        embed.add_field(
            name="__Invalid Embed Data__",
            value=(
                "In cases where the AI fails to generate valid embed data, ensure your description is clear and specific. Retry the command or modify your prompt for better results."
            ),
            inline=False
        )
        embed.add_field(
            name="__Button Malfunctions__",
            value=(
                "If buttons aren't responding, check if the manual has timed out. Refresh the manual by reissuing the `/embed manual` command."
            ),
            inline=False
        )
        embed.add_field(
            name="__Contact Support__",
            value=(
                "If issues persist, use the `/suggestion` command to report the problem. Provide detailed information to help the support team assist you effectively."
            ),
            inline=False
        )
        embed.set_footer(
            text="-# Navigation - Use the ⬅️ and ➡️ buttons to navigate through the pages. The 🏠 button will bring you back to this introduction."
        )
        embed.set_author(
            name="Page 15 | Troubleshooting Common Issues",
            icon_url=self.bot.user.avatar.url if self.bot.user.avatar else discord.Embed.Empty
        )
        pages.append(embed)

        # Page 16: Frequently Asked Questions (FAQ)
        embed = discord.Embed(
            title="<:7664book:1204768405513834576> **Frequently Asked Questions (FAQ)**",
            description=(
                "Find answers to the most commonly asked questions about embed creation and management."
            ),
            color=random.choice(colors)
        )
        embed.add_field(
            name="__Q1: How do I update an existing embed?__",
            value=(
                "A: Use the same creation commands with the existing embed name. For example, to update the title:\n```/embed title <embed_name> <new_title>```"
            ),
            inline=False
        )
        embed.add_field(
            name="__Q2: Can I share my saved embeds with others?__",
            value=(
                "A: Currently, embeds are saved per user. To share, you can copy the embed's details or use the AI generation feature to recreate it."
            ),
            inline=False
        )
        embed.add_field(
            name="__Q3: What happens if my embed exceeds the size limits?__",
            value=(
                "A: The bot will notify you if any part of the embed exceeds Discord's size limitations. You'll need to shorten the respective sections."
            ),
            inline=False
        )
        embed.add_field(
            name="__Q4: How do I add multiple fields to an embed?__",
            value=(
                "A: Use the `*/embed field add*` command repeatedly to add multiple fields. Each field can contain a name, value, and an optional inline property."
            ),
            inline=False
        )
        embed.add_field(
            name="__Q5: Can I customize button actions beyond the default options?__",
            value=(
                "A: Yes! With Custom ID buttons, you can define specific actions by collaborating with a developer to implement custom behaviors."
            ),
            inline=False
        )
        embed.set_footer(
            text="-# Navigation - Use the ⬅️ and ➡️ buttons to navigate through the pages. The 🏠 button will bring you back to this introduction."
        )
        embed.set_author(
            name="Page 16 | Frequently Asked Questions (FAQ)",
            icon_url=self.bot.user.avatar.url if self.bot.user.avatar else discord.Embed.Empty
        )
        pages.append(embed)

        # Page 17: Contact and Support Information
        embed = discord.Embed(
            title="<:server:1204686780775923753> **Contact and Support Information**",
            description=(
                "Need assistance or have suggestions? Here's how to get in touch with the support team."
            ),
            color=random.choice(colors)
        )
        embed.add_field(
            name="__Support Server__",
            value=(
                "Join our [Support Server](https://discord.gg/ncXQSvwPre) to ask questions, report issues, and connect with other users."
            ),
            inline=False
        )
        embed.add_field(
            name="__Reporting Issues__",
            value=(
                "Use the `/suggestion` command within the bot to submit bug reports or feature requests."
            ),
            inline=False
        )
        embed.add_field(
            name="__Developer Contact__",
            value=(
                "Reach out directly to the developer via [GitHub](https://github.com/your-profile) or [Twitter](https://twitter.com/your-handle)."
            ),
            inline=False
        )
        embed.add_field(
            name="__Helpful Links__",
            value=(
                "• [Bot Documentation](https://yourdocumentation.com)\n"
                "• [GitHub Repository](https://github.com/your-repo)\n"
                "• [Feature Roadmap](https://yourroadmap.com)"
            ),
            inline=False
        )
        embed.set_footer(
            text="-# Navigation - Use the ⬅️ and ➡️ buttons to navigate through the pages. The 🏠 button will bring you back to this introduction."
        )
        embed.set_author(
            name="Page 17 | Contact and Support Information",
            icon_url=self.bot.user.avatar.url if self.bot.user.avatar else discord.Embed.Empty
        )
        pages.append(embed)

        # Page 18: Changelog and Updates
        embed = discord.Embed(
            title="<:3753star:1233771382559473735> **Changelog and Updates**",
            description=(
                "Stay updated with the latest features, improvements, and bug fixes implemented in the bot."
            ),
            color=random.choice(colors)
        )
        embed.add_field(
            name="__Version 2.0__",
            value=(
                "• Introduced **AI Embed Generation** for automated embed creation.\n"
                "• Enhanced **Embed Builder** with new customization options.\n"
                "• Fixed bugs related to **button interactions**."
            ),
            inline=False
        )
        embed.add_field(
            name="__Version 1.5__",
            value=(
                "• Added **Manual Embed Creation** commands for advanced users.\n"
                "• Improved **Embed Management** with better listing and deletion options.\n"
                "• Optimized performance for faster embed rendering."
            ),
            inline=False
        )
        embed.add_field(
            name="__Version 1.0__",
            value=(
                "• Initial release of the **Embed Guide**.\n"
                "• Basic embed creation and management features.\n"
                "• Introduction of the **Embed Builder**."
            ),
            inline=False
        )
        embed.set_footer(
            text="-# Navigation - Use the ⬅️ and ➡️ buttons to navigate through the pages. The 🏠 button will bring you back to this introduction."
        )
        embed.set_author(
            name="Page 18 | Changelog and Updates",
            icon_url=self.bot.user.avatar.url if self.bot.user.avatar else discord.Embed.Empty
        )
        pages.append(embed)

        return pages

class EmbedManual(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.embed_pages = EmbedPages(bot)

    @commands.hybrid_command(
        name="embed_manual",
        description="Shows a comprehensive guide on how to create and manage embeds."
    )
    async def embed_manual(self, ctx):
        """Sends the embed manual with navigation buttons."""
        view = EmbedManualView(self.embed_pages.pages)
        await ctx.send(embed=self.embed_pages.pages[0], view=view)

async def setup(bot: commands.Bot):
    await bot.add_cog(EmbedManual(bot))
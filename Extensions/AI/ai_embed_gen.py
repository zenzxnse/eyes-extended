import discord
from discord.ext import commands
from discord import app_commands
from Augmentations.Ai.GenEmbed import gen_embed
from Augmentations.eyehelper import load_instruction
from Extensions.Utility.embed import EmbedProject
import re
import random

class AI_Embed_Gen(commands.GroupCog, name="ai", description="Generate embeds using AI"):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.embed_project = EmbedProject(bot)
        self.instructions = load_instruction("Augmentations/Ai/ET.txt")

    embed = app_commands.Group(name="embed", description="Generate embeds using AI")
    
    @embed.command(name="generate", description="Generate an embed using AI")
    async def aiEmbedGenerate(self, interaction: discord.Interaction, description: str):
        await interaction.response.defer()
        
        # Check if user has reached the embed limit
        user_embeds = await self.embed_project.get_user_embeds(interaction.user.id)
        if len(user_embeds) >= 25:
            await interaction.followup.send("You have reached the maximum limit of 25 embeds. Please delete some embeds using the `*delete <embed name>` command and view your embeds using the `/embed list` command.", ephemeral=True)
            return

        # Generate embed data using AI
        ai_response = await gen_embed(
            history=[{"role": "user", "content": f"Generate an embed based on this description: {description}"}],
            instructions=self.instructions,
        )
        
        embed_data = self.extract_embed_data(ai_response)
        
        # If invalid embed data, try regenerating once
        if not embed_data:
            ai_response = await gen_embed(
                history=[{"role": "user", "content": f"{description}\n\nPlease carefully review and fix the previous response. There was an issue with the generated embed data."}],
            )
            embed_data = self.extract_embed_data(ai_response)
        
        if not embed_data:
            await interaction.followup.send("Sorry, I couldn't generate a valid embed based on your description. Please try again with a different prompt.", ephemeral=True)
            return

        # Handle duplicate embed names
        original_name = embed_data['name']
        counter = 1
        while await self.embed_project.embed_exists(interaction.user.id, embed_data['name']):
            embed_data['name'] = f"{original_name}_{counter}"
            counter += 1

        # Save the embed
        try:
            await self.embed_project.save_user_embeds(
                interaction.user.id,
                embed_data['name'],
                title=embed_data['title'],
                description=embed_data['description'],
                color=embed_data['color'],
                thumbnail_url=embed_data['thumbnail_url'],
                image_url=embed_data['image_url'],
                footer_text=embed_data['footer_text'],
                footer_icon_url=embed_data['footer_icon_url'],
                author_text=embed_data['author_text'],
                author_icon_url=embed_data['author_icon_url']
            )

            for field in embed_data['fields']:
                await self.embed_project.add_field_to_embed(
                    interaction.user.id,
                    embed_data['name'],
                    field['name'],
                    field['value'],
                    field['inline']
                )

            embed = await self.embed_project.retrieve_embed_data(interaction.user.id, embed_data['name'])
            await interaction.followup.send(f"Embed '{embed_data['name']}' created successfully! You can view it using the `*show {embed_data['name']}` command.", embed=embed)
        except Exception as e:
            await interaction.followup.send(f"An error occurred while saving the embed: {str(e)}. Please try again later or use the `/suggestion` command to report this issue.", ephemeral=True)

    def extract_embed_data(self, ai_response):
        # Extract embed properties using regex
        title_match = re.search(r'\[title \{-m (.*?)\}\]', ai_response)
        description_match = re.search(r'\[description \{-m (.*?)\}\]', ai_response)
        color_match = re.search(r'\[color \{-h ([A-Fa-f0-9]{6})\}\]', ai_response)
        thumbnail_match = re.search(r'\[thumbnail \{-l (.*?)\}\]', ai_response)
        image_match = re.search(r'\[image \{-l (.*?)\}\]', ai_response)
        footer_text_match = re.search(r'\[footer_text \{-m (.*?)\}\]', ai_response)
        footer_icon_match = re.search(r'\[footer_icon \{-l (.*?)\}\]', ai_response)
        author_text_match = re.search(r'\[author_text \{-m (.*?)\}\]', ai_response)
        author_icon_match = re.search(r'\[author_icon \{-l (.*?)\}\]', ai_response)
        field_matches = re.findall(r'\[field \{fn \{-m (.*?)\} value \{-m (.*?)\} inline \{(0|1)\}\}\]', ai_response)
        name_match = re.search(r'-n "(.*?)"', ai_response)

        if not title_match or not name_match:
            return None
        
        # Ensure color is valid
        if color_match:
            try:
                color = int(color_match.group(1), 16)
            except ValueError:
                color = 0x000000  # Default to black if invalid
        else:
            color = 0x000000

        embed_data = {
            "title": title_match.group(1).replace('\\n', '\n'),
            "description": description_match.group(1).replace('\\n', '\n') if description_match else "",
            "color": color,
            "thumbnail_url": thumbnail_match.group(1) if thumbnail_match else None,
            "image_url": image_match.group(1) if image_match else None,
            "footer_text": footer_text_match.group(1) if footer_text_match else None,
            "footer_icon_url": footer_icon_match.group(1) if footer_icon_match else None,
            "author_text": author_text_match.group(1) if author_text_match else None,
            "author_icon_url": author_icon_match.group(1) if author_icon_match else None,
            "name": name_match.group(1),
            "fields": [
                {"name": name[:256], "value": value[:1024], "inline": bool(int(inline))}
                for name, value, inline in field_matches
            ][:25]  # Limit to 25 fields
        }

        return embed_data

async def setup(bot: commands.Bot):
    await bot.add_cog(AI_Embed_Gen(bot))
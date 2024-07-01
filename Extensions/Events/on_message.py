import discord
from discord.ext import commands
from Augmentations.Ai.Gen_response import gen_response
from Augmentations.eyehelper import load_instruction
import time, re
from Extensions.Utility.embed import EmbedProject  # Make sure this import is present
from colorama import Fore, Style

COOLDOWN_TIME = 2
MAX_HISTORY = 10
BOT_ID = 1113819181280940112

class OnMessage(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.channel_histories = {}
        self.user_cooldowns = {}  
        self.instructions = load_instruction("Augmentations/Ai/basic_instructions.txt")
        self.embed_project = EmbedProject(bot)  # Initialize EmbedProject

    async def process_embed_command(self, message, command):
        
        if message.author.id != self.bot.user.id and message.author.id != BOT_ID:
            await message.channel.send("Nuh uh.")
            return
        
        command = command[command.index('*embed'):]
        
        print(f"Processing embed command: {command}")
        # Extract embed properties
        title_match = re.search(r'\[title \{-m (.*?)\}\]', command)
        description_match = re.search(r'\[description \{-m (.*?)\}\]', command)
        thumbnail_match = re.search(r'\[thumbnail \{-l (.*?)\}\]', command)
        image_match = re.search(r'\[image \{-l (.*?)\}\]', command)
        footer_text_match = re.search(r'\[footer_text \{-m (.*?)\}\]', command)
        footer_icon_match = re.search(r'\[footer_icon \{-l (.*?)\}\]', command)
        author_text_match = re.search(r'\[author_text \{-m (.*?)\}\]', command)
        author_icon_match = re.search(r'\[author_icon \{-l (.*?)\}\]', command)
        field_matches = re.findall(r'\[field \{fn \{-m (.*?)\} value \{-m (.*?)\} inline \{(0|1)\}\}\]', command)
        name_match = re.search(r'-n "(.*?)"', command)
        user_match = re.search(r'-u <@(\d+)>', command)

        print(f"Matches - Title: {title_match}, Description: {description_match}, Name: {name_match}, User: {user_match}")
        print(f"Field matches: {field_matches}")

        if not (title_match and name_match and user_match):
            await message.channel.send("Invalid embed command format.")
            return

        title = title_match.group(1).replace('\\n', '\n')
        description = description_match.group(1).replace('\\n', '\n') if description_match else ""
        thumbnail = thumbnail_match.group(1) if thumbnail_match else None
        image = image_match.group(1) if image_match else None
        footer_text = footer_text_match.group(1) if footer_text_match else None
        footer_icon = footer_icon_match.group(1) if footer_icon_match else None
        author_text = author_text_match.group(1) if author_text_match else None
        author_icon = author_icon_match.group(1) if author_icon_match else None
        embed_name = name_match.group(1)
        user_id = int(user_match.group(1))

        print(f"Parsed data - Title: {title}, Description: {description}, Embed Name: {embed_name}, User ID: {user_id}")
        print(f"Image: {image}, Thumbnail: {thumbnail}")
        print(f"Number of fields: {len(field_matches)}")

        embed_data = {
            "title": title,
            "description": description,
            "thumbnail_url": thumbnail,
            "image_url": image,
            "footer_text": footer_text,
            "footer_icon_url": footer_icon,
            "author_text": author_text,
            "author_icon_url": author_icon,
        }

        print(f"Embed data: {embed_data}")
        
        embed_name = name_match.group(1)
        user_id = int(user_match.group(1))

        # Check if the embed already exists
        existing_embed = await self.embed_project.retrieve_embed_data(user_id, embed_name)
        if existing_embed:
            error_message = f"An embed named '{embed_name}' already exists in the user account. Try a different name."
            
            # Generate AI response with the error message
            ai_response = await gen_response(
                history=[
                    {"role": "user", "content": command},
                    {"role": "system", "content": error_message + " Please provide a new embed command with a different name using the exact same format as before, starting with '*embed'."}
                ],
                instructions=self.instructions,
                user_name=message.author.name,
                user_mention=f"<@{message.author.id}>"
            )
            
            # Check if the AI response starts with '*embed', if not, prepend it
            if not ai_response.startswith('*embed'):
                ai_response = '*embed ' + ai_response

            await message.channel.send(ai_response)
            print(f"{Fore.RED}Embed command failed: {Style.RESET_ALL}{ai_response}")
            return

        try:
            # Save the basic embed data
            await self.embed_project.save_user_embeds(user_id, embed_name, **embed_data)
            print(f"Embed saved successfully for user {user_id}")

            # Add fields using the add_field_to_embed method
            for index, field_match in enumerate(field_matches, start=1):
                field_name = field_match[0][:256]  # Limit to 256 characters (Discord's limit)
                field_value = field_match[1][:1024]  # Limit to 1024 characters
                field_inline = bool(int(field_match[2]))
                await self.embed_project.add_field_to_embed(user_id, embed_name, index, field_name, field_value, field_inline)
            
            print(f"Fields added successfully")
        except Exception as e:
            print(f"Error saving embed or adding fields: {str(e)}")
            await message.channel.send("An error occurred while saving the embed or adding fields.")
            return

        # Retrieve and send the created embed
        try:
            embed = await self.embed_project.retrieve_embed_data(user_id, embed_name)
            if embed:
                await message.channel.send(f"Embed '{embed_name}' created for <@{user_id}>:", embed=embed)
                print(f"Embed sent successfully")
            else:
                await message.channel.send("Failed to create the embed.")
                print(f"Failed to retrieve the created embed")
        except Exception as e:
            print(f"Error retrieving or sending embed: {str(e)}")
            await message.channel.send("An error occurred while retrieving or sending the embed.")
            

    @commands.Cog.listener()
    async def on_message(self, message):
        # Special check for embed command
        if message.author.id == 717037473401667634 and message.content.startswith("gg"):
            await message.channel.send("gg")
            return
        if '*embed' in message.content:
            print(f"Embed command detected: {message.content}")
            await self.process_embed_command(message, message.content)
            return

        # Existing checks for other cases
        bot_prefixes = ("&", "*", "^")
        if message.author.bot:
            return
        if message.content.startswith(bot_prefixes):
            return

        is_mentioned = self.bot.user.mentioned_in(message) and not message.mention_everyone
        
        if is_mentioned:
            user_id = message.author.id
            current_time = time.time()

            # Check if the user is on cooldown
            if user_id in self.user_cooldowns:
                time_since_last_interaction = current_time - self.user_cooldowns[user_id]
                if time_since_last_interaction < COOLDOWN_TIME:
                    seconds_left = COOLDOWN_TIME - time_since_last_interaction
                    await message.reply(f"You are on cooldown. Please wait {int(seconds_left)} seconds.", mention_author=False)
                    return
                
            # Update the last interaction time for the user
            self.user_cooldowns[user_id] = current_time

            channel_id = message.channel.id
            if channel_id not in self.channel_histories:
                self.channel_histories[channel_id] = []

            if message.content.strip() == f"<@{self.bot.user.id}>":
                await message.reply("Info on how to use the bot\n```None```", mention_author=False)
            else:
                async with message.channel.typing():
                    self.channel_histories[channel_id].append({"role": "user", "content": message.content})
                    
                    if len(self.channel_histories[channel_id]) > MAX_HISTORY:
                        self.channel_histories[channel_id].pop(0)
                    
                    response = await gen_response(
                        instructions=self.instructions,
                        history=self.channel_histories[channel_id],
                        user_name=message.author.name,
                        user_mention=f"<@{message.author.id}>"
                    )
                    self.channel_histories[channel_id].append({"role": "assistant", "content": response})
                    if len(self.channel_histories[channel_id]) > MAX_HISTORY:
                        self.channel_histories[channel_id].pop(0)
                    for i in range(0, len(response), 2000):
                        await message.reply(response[i:i+2000], mention_author=False)
                    
async def setup(bot):
    await bot.add_cog(OnMessage(bot))
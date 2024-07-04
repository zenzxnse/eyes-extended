import discord
from discord.ext import commands
from Augmentations.Ai.Gen_response import gen_response
from Augmentations.eyehelper import load_instruction
from Augmentations.Optimizations.Eyes_commands import perform_search, process_embed_command
from Extensions.Utility.embed import EmbedProject
import time, re
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
        self.embed_project = EmbedProject(bot)

    def update_channel_history(self, channel_id, role, content):
        if channel_id not in self.channel_histories:
            self.channel_histories[channel_id] = []
        
        self.channel_histories[channel_id].append({"role": role, "content": content})
        
        if len(self.channel_histories[channel_id]) > MAX_HISTORY:
            self.channel_histories[channel_id].pop(0)
        
        print(f"{Fore.GREEN}Updated history for channel {channel_id}: {self.channel_histories[channel_id]}{Style.RESET_ALL}")

    @commands.Cog.listener()
    async def on_message(self, message):
        if message.author.id == 717037473401667634 and message.content.startswith("gg"):
            await message.channel.send("gg")
            return

        if message.content.startswith('*search '):
            query = re.search(r'"([^"]*)"', message.content[8:])
            query = query.group(1) if query else message.content[8:].strip()
            query = query[:200]  # Limit query to 200 characters

            print(Fore.CYAN + f"Search query: {query}" + Style.RESET_ALL)

            result = await perform_search(query)
            
            self.update_channel_history(message.channel.id, "user", f"*search {query}")
            
            if isinstance(result, tuple) and len(result) == 2:
                response, embed = result
                self.update_channel_history(message.channel.id, "assistant", response)
                await message.channel.send(response, embed=embed)
            else:
                response = str(result)
                self.update_channel_history(message.channel.id, "assistant", response)
                await message.channel.send(response)
            
            return

        if '*embed' in message.content:
            await process_embed_command(message, message.content, self.embed_project, self.instructions)
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

            if message.content.strip() == f"<@{self.bot.user.id}>":
                await message.reply("Info on how to use the bot\n```None```", mention_author=False)
            else:
                async with message.channel.typing():
                    self.update_channel_history(message.channel.id, "user", message.content)
                    
                    response = await gen_response(
                        instructions=self.instructions,
                        history=self.channel_histories[message.channel.id],
                        user_name=message.author.name,
                        user_mention=f"<@{message.author.id}>"
                    )
                    self.update_channel_history(message.channel.id, "assistant", response)
                    for i in range(0, len(response), 2000):
                        await message.reply(response[i:i+2000], mention_author=False)
        else:
            # Track all messages in channels where the bot has been active
            if message.channel.id in self.channel_histories:
                self.update_channel_history(message.channel.id, "user", message.content)

async def setup(bot):
    await bot.add_cog(OnMessage(bot))
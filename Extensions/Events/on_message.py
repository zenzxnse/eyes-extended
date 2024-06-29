import discord
from discord.ext import commands
from Augmentations.Ai.Gen_response import gen_response
from Augmentations.eyehelper import load_instruction
import time

COOLDOWN_TIME = 2
MAX_HISTORY = 10

class OnMessage(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.channel_histories = {}
        self.user_cooldowns = {}  
        self.instructions = load_instruction("Augmentations/Ai/basic_instructions.txt")

    @commands.Cog.listener()
    async def on_message(self, message):
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
                
            # if not message.author.guild_permissions.administrator:
            #     await message.reply("Only administrators can interact with Ai, you may dm the bot.", mention_author=False)
            #     return
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
                    
                    response = await gen_response(instructions=self.instructions, history=self.channel_histories[channel_id])  # Pass history as a list
                    self.channel_histories[channel_id].append({"role": "assistant", "content": response})
                    if len(self.channel_histories[channel_id]) > MAX_HISTORY:
                        self.channel_histories[channel_id].pop(0)
                    for i in range(0, len(response), 2000):
                        await message.reply(response[i:i+2000], mention_author=False)

async def setup(bot):
    await bot.add_cog(OnMessage(bot))
import discord
from discord.ext import commands
from colorama import Fore, Style
import time
from Global import config
import random
import asyncio
import requests

# NAGA_KEY = config['API_KEYS']['NAGA_KEY_1']

# def fetch_chat_models():
#     models = []
#     headers = {
#         'Authorization': f'Bearer {NAGA_KEY}',
#         'Content-Type': 'application/json'
#     }

#     response = requests.get('https://api.naga.ac/v1/models', headers=headers)
#     if response.status_code == 200:
#         ModelsData = response.json()
#         models.extend(
#             model['id']
#             for model in ModelsData.get('data')
#             if "max_images" not in model
#         )
#     else:
#         print(f"Failed to fetch chat models. Status code: {response.status_code}")

#     return models

# chat_models = fetch_chat_models()
# model_blob = "\n".join(chat_models)

NUMBERS = {
    0 : "零",
    1 : "一",
    2 : "二",
    3 : "三",
    4 : "四",
    5 : "五",
    6 : "六",
    7 : "七",
    8 : "八",
    9 : "九"
}

def matrix(number):
    return ''.join(NUMBERS[int(digit)] for digit in str(number))

class OnReady(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_ready(self):
        print(Fore.CYAN + Style.BRIGHT + f"🟩🌐 {self.bot.user} aka {self.bot.user.name} has connected to Discord!")
        invite_link = discord.utils.oauth_url(self.bot.user.id, permissions=discord.Permissions(administrator=True), scopes=("bot", "applications.commands"))
        print(Fore.GREEN + f"Invite link: {invite_link}")
        print(f"Today at {time.strftime('%H:%M:%S')}")
        # print(f"\033[1;38;5;202mAvailable models: {model_blob}\033[0m")
        print(f"\033[1;38;5;46mCurrent model: {config['MODEL_ID']}\033[0m")

        activity_config = config['Activity_Type']
        activity_type = activity_config['type']
        activity_name = activity_config['name']
        activity_state = activity_config['state']

        if activity_type == "Playing" and activity_state == "Random":
            while True:
                random_number = random.randint(111111111111111, 999999999999999)
                japanese_number = matrix(random_number)
                activity_name_with_number = f"{activity_name} {japanese_number}"
                await self.bot.change_presence(activity=discord.Game(name=activity_name_with_number))
                await asyncio.sleep(7)
        elif activity_type == "Playing":
            await self.bot.change_presence(activity=discord.Game(name=activity_name))
        elif activity_type == "Watching":
            await self.bot.change_presence(activity=discord.Activity(type=discord.ActivityType.watching, name=activity_name))
        elif activity_type == "Streaming":
            await self.bot.change_presence(activity=discord.Streaming(name=activity_name, url=activity_state))
        elif activity_type == "Listening":
            await self.bot.change_presence(activity=discord.Activity(type=discord.ActivityType.listening, name=activity_name))
        elif activity_type == "Custom": # This displays the activity as a custom status
            await self.bot.change_presence(activity=discord.CustomActivity(name=activity_name, state=activity_state))
        else:
            print(Fore.RED + Style.BRIGHT + f"🔴🔴🔴 Invalid activity type: {activity_type}, using default activity type: Playing")
            await self.bot.change_presence(activity=discord.Game(name="🌐 https://discord.gg/vqQ3ZJZN"))

async def setup(bot):
    await bot.add_cog(OnReady(bot))


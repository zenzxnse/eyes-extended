from .Utility import UTILITY
from .Events import EVENTS
from .Commands import COMMANDS
from .Games import GAMES
from .Moderation import MODERATION
from .AI import AI
from .Help import HELP
from colorama import Fore, Style
import asyncio

async def load_extensions(bot):
    loading_emoji = "🔃"
    success_emoji = "✅"
    error_emoji = "❌"

    for cog in UTILITY:
        cog_name = cog.split('.')[-1]
        print(f"{Fore.GREEN}{loading_emoji} Loading Command {cog_name}...{Style.RESET_ALL}")
        try:
            await bot.load_extension(cog)
            print(f"{Fore.GREEN}{success_emoji} Loaded Command {cog_name}{Style.RESET_ALL}")
        except Exception as e:
            print(f"{Fore.RED}{error_emoji} Could not load Command {cog_name}: {e}{Style.RESET_ALL}")

    for cog in EVENTS:
        cog_name = cog.split('.')[-1]
        print(f"{Fore.GREEN}{loading_emoji} Loading Event Handler {cog_name}...{Style.RESET_ALL}")
        try:
            await bot.load_extension(cog)
            print(f"{Fore.GREEN}{success_emoji} Loaded Event Handler {cog_name}{Style.RESET_ALL}")
        except Exception as e:
            print(f"{Fore.RED}{error_emoji} Could not load Event Handler {cog_name}: {e}{Style.RESET_ALL}")

    for cog in COMMANDS:
        cog_name = cog.split('.')[-1]
        print(f"{Fore.GREEN}{loading_emoji} Loading Command {cog_name}...{Style.RESET_ALL}")
        try:
            await bot.load_extension(cog)
            print(f"{Fore.GREEN}{success_emoji} Loaded Command {cog_name}{Style.RESET_ALL}")
        except Exception as e:
            print(f"{Fore.RED}{error_emoji} Could not load Command {cog_name}: {e}{Style.RESET_ALL}")

    for cog in GAMES:
        cog_name = cog.split('.')[-1]
        print(f"{Fore.GREEN}{loading_emoji} Loading Game {cog_name}...{Style.RESET_ALL}")
        try:
            await bot.load_extension(cog)
            print(f"{Fore.GREEN}{success_emoji} Loaded Game {cog_name}{Style.RESET_ALL}")
        except Exception as e:
            print(f"{Fore.RED}{error_emoji} Could not load Game {cog_name}: {e}{Style.RESET_ALL}")

    for cog in MODERATION:
        cog_name = cog.split('.')[-1]
        print(f"{Fore.GREEN}{loading_emoji} Loading Moderation {cog_name}...{Style.RESET_ALL}")
        try:
            await bot.load_extension(cog)
            print(f"{Fore.GREEN}{success_emoji} Loaded Moderation {cog_name}{Style.RESET_ALL}")
        except Exception as e:
            print(f"{Fore.RED}{error_emoji} Could not load Moderation {cog_name}: {e}{Style.RESET_ALL}")

    for cog in AI:
        cog_name = cog.split('.')[-1]
        print(f"{Fore.GREEN}{loading_emoji} Loading AI {cog_name}...{Style.RESET_ALL}")
        try:
            await bot.load_extension(cog)
            print(f"{Fore.GREEN}{success_emoji} Loaded AI {cog_name}{Style.RESET_ALL}")
        except Exception as e:
            print(f"{Fore.RED}{error_emoji} Could not load AI {cog_name}: {e}{Style.RESET_ALL}")
            
    for cog in HELP:
        cog_name = cog.split('.')[-1]
        print(f"{Fore.GREEN}{loading_emoji} Loading Help {cog_name}...{Style.RESET_ALL}")
        try:
            await bot.load_extension(cog)
            print(f"{Fore.GREEN}{success_emoji} Loaded Help {cog_name}{Style.RESET_ALL}")
        except Exception as e:
            print(f"{Fore.RED}{error_emoji} Could not load Help {cog_name}: {e}{Style.RESET_ALL}")
            
    

if __name__ == "__main__":
    asyncio.run(load_extensions())


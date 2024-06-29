from openai import AsyncOpenAI
from Global import config
import json
import os
import re
from datetime import datetime
import aiohttp
import discord

internet_access = config['INTERNET_ACCESS']

client = AsyncOpenAI(
    base_url=config['API_BASE_URL'],
    api_key=config['API_KEYS']['API_KEY_4'],
)
default_instructions = "You are a 目付き(Eyes) a discord bot, you are working in a confidential environment, keep your responses short and concise, and don't mention your name or mention the user unless it is necessary. only answer relevant questions, and don't make up new information. if you don't know the answer, say so, and don't make up new information. Provide detailed yet concise info about the search query, you have internet access."

async def ai_internet_search(history, instructions=default_instructions):
    messages = [
        {"role": "system", "name": "instructions", "content": instructions},
        *history,
    ]

    tools = [
        {
            "type": "function",
            "function": {
                "name": "searchtool",
                "description": "Searches the internet.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "query": {
                            "type": "string",
                            "description": "The query for search engine",
                        }
                    },
                    "required": ["query"],
                },
            },
        }
    ]
    try:
        response = await client.chat.completions.create(
            model=config['MODEL_ID'],
            messages=messages,        
            tools=tools,
            tool_choice="auto",
        )
    except Exception as e:
        return f"Error in creating completion: {e}", None

    response_message = response.choices[0].message
    tool_calls = response_message.tool_calls

    if tool_calls:
        available_functions = {
            "searchtool": search,
        }
        messages.append(response_message)

        for tool_call in tool_calls:
            function_name = tool_call.function.name
            function_to_call = available_functions.get(function_name)
            if not function_to_call:
                return f"Function {function_name} not found.", None

            function_args = json.loads(tool_call.function.arguments)
            try:
                function_response, embed = await function_to_call(
                    prompt=function_args.get("query")
                )
            except Exception as e:
                return f"Error calling function {function_name}: {e}", None

            messages.append(
                {
                    "tool_call_id": tool_call.id,
                    "role": "tool",
                    "name": function_name,
                    "content": function_response,
                }
            )
        try:
            second_response = await client.chat.completions.create(
                model=config['MODEL_ID'],
                messages=messages
            )
        except Exception as e:
            return f"Error in creating second completion: {e}", None
        
        return second_response.choices[0].message.content, embed
    return response_message.content, None

async def search(prompt):
    """
    Asynchronously searches for a prompt using Google Custom Search API and returns the search results as a blob.

    Args:
        prompt (str): The prompt to search for.

    Returns:
        tuple: The search results as a blob and an optional embed.

    Raises:
        None
    """
    if not internet_access or len(prompt) > 200:
        return "Internet access is disabled or the prompt is too long.", None
    
    search_results_limit = config['MAX_SEARCH_RESULTS']

    url = "https://www.googleapis.com/customsearch/v1"
    querystring = {
        "key": "AIzaSyARjNLIiLdSnrH-dQr-6krLFJI2RgsCUGE",
        "cx": "23485fccf50b645f4",  # Your actual search engine ID
        "q": prompt
    }

    current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    blob = f"Search results for: '{prompt}' at {current_time}:\n"
    embed = None
    
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(url, params=querystring) as response:
                search_results = await response.json()
    except aiohttp.ClientError as e:
        return f"An error occurred during the search request: {e}", None

    if 'items' in search_results:
        for index, result in enumerate(search_results['items'][:search_results_limit]):
            try:
                title = result.get('title', 'No title')
                snippet = result.get('snippet', 'No snippet')
                link = result.get('link', 'No URL')
                blob += f'[{index}] Title: {title}\nSnippet: {snippet}\nURL: {link}\n\n'
                
                # Create embed for the first result with an image
                if index == 0 and 'pagemap' in result and 'cse_image' in result['pagemap']:
                    image_url = result['pagemap']['cse_image'][0].get('src', None)
                    if image_url:
                        embed = discord.Embed(title=title, description=snippet, url=link)
                        embed.set_thumbnail(url=image_url)
            except Exception as e:
                blob += f'Search error: {e}\n'
        blob += "\nSearch results allow you to have real-time information and the ability to browse the internet. As the links were generated by the system rather than the user, please send a response along with the link if necessary.\n"
    else:
        blob += "No search results found."

    return blob, embed
import aiohttp
import discord
from Global import config
import json
from datetime import datetime

YOUTUBE_API_KEY = config['API_KEYS']['YOUTUBE_API_KEY']
YOUTUBE_SEARCH_URL = "https://www.googleapis.com/youtube/v3/search"

async def youtube_search(query, max_results=5):
    params = {
        "part": "snippet",
        "q": query,
        "key": YOUTUBE_API_KEY,
        "maxResults": max_results,
        "type": "video"
    }

    async with aiohttp.ClientSession() as session:
        async with session.get(YOUTUBE_SEARCH_URL, params=params) as response:
            if response.status != 200:
                return f"Error: {response.status}", None
            data = await response.json()

    results = data.get("items", [])
    if not results:
        return "No results found.", None

    blob = f"Search results for: '{query}' at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}:\n"
    embed = None

    for index, item in enumerate(results):
        title = item["snippet"]["title"]
        description = item["snippet"]["description"]
        video_id = item["id"]["videoId"]
        video_url = f"https://www.youtube.com/watch?v={video_id}"
        blob += f"[{index + 1}] Title: {title}\nDescription: {description}\nURL: {video_url}\n\n"

        if index == 0:
            embed = discord.Embed(title=title, description=description, url=video_url)
            embed.set_thumbnail(url=item["snippet"]["thumbnails"]["high"]["url"])

    return blob, embed
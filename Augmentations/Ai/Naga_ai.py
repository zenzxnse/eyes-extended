from openai import AsyncOpenAI
import os
from Global import config


openai_client = AsyncOpenAI(
    api_key = config['API_KEYS']['NAGA_KEY'],
    base_url = "https://api.naga.ac/v1"
)
default_instructions = "You are a 目付き(Eyes) a discord bot, you are working in a confidential environment, keep your responses short and concise, and don't mention your name or mention the user unless it is necessary. only answer relevant questions, and don't make up new information. if you don't know the answer, say so, and don't make up new information."
async def gen_response(history, instructions=default_instructions):
    messages = [
            {"role": "system", "name": "instructions", "content": instructions},
            *history,
        ]
    response = await openai_client.chat.completions.create(
        model=config['MODEL_ID'],
        messages=messages
    )
    message = response.choices[0].message.content
    return message


# 'gemini-1.5-pro-latest', 'gemini-1.5-flash-latest', 'gpt-4o', 'gpt-4o-2024-05-13', 'gpt-4-turbo', 'gpt-4-turbo-2024-04-09', 'gpt-4-vision-preview', 'gpt-4-1106-vision-preview', 'gpt-4-turbo-preview', 'gpt-4-0125-preview', 'gpt-4-1106-preview', 'gpt-4', 'gpt-4-0613', 'llama-3-70b-instruct', 'llama-3-8b-instruct', 'mixtral-8x22b-instruct', 'command-r-plus', 'command-r', 'codestral', 'codestral-2405', 'mistral-large', 'mistral-large-2402', 'mistral-next', 'mistral-small', 'mistral-small-2402', 'gpt-3.5-turbo', 'gpt-3.5-turbo-0125', 'gpt-3.5-turbo-1106', 'gpt-3.5-turbo-0613', 'claude-3-opus', 'claude-3-opus-20240229', 'claude-3-sonnet', 'claude-3-sonnet-20240229', 'claude-3-haiku', 'claude-3-haiku-20240307', 'claude-2.1', 'claude-instant', 'gemini-pro', 'gemini-pro-vision', 'llama-2-70b-chat', 'llama-2-13b-chat', 'llama-2-7b-chat', 'mistral-7b-instruct' or 'mixtral-8x7b-instruct'", 'input': 'gpt-3.5-turb', 'ctx': {'expected': "'gemini-1.5-pro-latest', 'gemini-1.5-flash-latest', 'gpt-4o', 'gpt-4o-2024-05-13', 'gpt-4-turbo', 'gpt-4-turbo-2024-04-09', 'gpt-4-vision-preview', 'gpt-4-1106-vision-preview', 'gpt-4-turbo-preview', 'gpt-4-0125-preview', 'gpt-4-1106-preview', 'gpt-4', 'gpt-4-0613', 'llama-3-70b-instruct', 'llama-3-8b-instruct', 'mixtral-8x22b-instruct', 'command-r-plus', 'command-r', 'codestral', 'codestral-2405', 'mistral-large', 'mistral-large-2402', 'mistral-next', 'mistral-small', 'mistral-small-2402', 'gpt-3.5-turbo', 'gpt-3.5-turbo-0125', 'gpt-3.5-turbo-1106', 'gpt-3.5-turbo-0613', 'claude-3-opus', 'claude-3-opus-20240229', 'claude-3-sonnet', 'claude-3-sonnet-20240229', 'claude-3-haiku', 'claude-3-haiku-20240307', 'claude-2.1', 'claude-instant', 'gemini-pro', 'gemini-pro-vision', 'llama-2-70b-chat', 'llama-2-13b-chat', 'llama-2-7b-chat', 'mistral-7b-instruct' or 'mixtral-8x7b-instruct'"}}], 'tip': None}}
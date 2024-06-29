from openai import AsyncOpenAI
import os
from Global import config

#docstring was generated through codeium ai

api_key = config['API_KEYS']['API_KEY_2']
client = AsyncOpenAI(base_url="https://api.groq.com/openai/v1/", api_key=api_key)

async def gen_response(history):
    """
    Generate a response using the OpenAI API.

    Args:
        history (list): The conversation history.

    Returns:
        str: The generated response message.
    """
    messages = [
        {"role": "system", "name": "instructions", "content": "You are a helpful assistant"},
        *history,
    ]

    # This Calls the AI API with the constructed messages
    try:
        response = await client.chat.completions.create(
            model=config['MODEL_ID'],
            messages=messages,
            tools=[], 
            tool_choice="auto",
        )
        response_message = response.choices[0].message.content
        return response_message
    except Exception as e:
        error_message = str(e)
        print(f"Failed to generate response: {error_message}")

        # If rate limit is reached, this handles the error
        if "Rate limit reached" in error_message:
            return "Rate limit reached. Please try again later."

        # if failed generation this is usually a json data error we simply take the response from the error and ignore it. dont wrap your mind aroun this.
        if "failed_generation" in error_message:
            start_idx = error_message.find("failed_generation") + len("failed_generation") + 3
            end_idx = error_message.find("}'", start_idx)
            failed_generation_content = error_message[start_idx:end_idx]
            formatted_response = failed_generation_content.replace("\\n", "\n").strip()
           
            unwanted_substring = """or more details.", 'type': 'invalid_request_error', 'code': 'tool_use_failed', 'failed_generation': '"""
            if unwanted_substring in formatted_response:
                formatted_response = formatted_response.replace(unwanted_substring, "").strip()
            return formatted_response
        return "An error occurred while generating the response. Please try again later."
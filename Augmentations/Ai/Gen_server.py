from groq import AsyncGroq
from Global import config
from Augmentations.eyehelper import load_instruction

api_keys = [
    config['API_KEYS']['API_KEY_1'],
    config['API_KEYS']['API_KEY_2'],
    config['API_KEYS']['API_KEY_3'],
    config['API_KEYS']['API_KEY_4'],
    config['API_KEYS']['API_KEY_5'],
]

clients = [AsyncGroq(api_key=key) for key in api_keys]
client_usage = {i: 0 for i in range(len(clients))}

async def gen_server(history, instructions='Augmentations/Ai/server_instruct.txt'):
    instructions = load_instruction(instructions)
    
    # Ensure history has a maximum of 5 items
    if len(history) > 5:
        history = history[-5:]
    
    messages = [
        {"role": "system", "content": instructions},
        *history,
    ]

    client_index = min(client_usage, key=client_usage.get)
    client = clients[client_index]
    client_usage[client_index] += 1

    try:
        stream = await client.chat.completions.create(
            model=config['MODEL_ID'],
            messages=messages,
            temperature=0.9,
            max_tokens=8192,
            top_p=1,
            stream=True,
        )

        response_message = ""
        async for chunk in stream:
            try:
                if chunk.choices[0].delta.content is not None:
                    response_message += chunk.choices[0].delta.content
            except (AttributeError, IndexError) as e:
                print(f"Error during streaming: {e}")
                print(f"Chunk data: {chunk}")

        client_usage[client_index] -= 1
        return response_message
    except Exception as e:
        error_message = str(e)
        print(f"Failed to generate response: {error_message}")
        client_usage[client_index] -= 1

        if "Rate limit reached" in error_message:
            next_client_index = (client_index + 1) % len(clients)
            return await gen_server(history, instructions)

        return "An error occurred while generating the server template. Please try again later."

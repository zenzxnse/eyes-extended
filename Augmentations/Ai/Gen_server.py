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
    # Determine which instructions to use
    if len(history) > 2 and "Please make the following changes to the template:" in history[-1]['content']:
        instruction_file = 'Augmentations/Ai/regenerate_instruct.txt'
    else:
        instruction_file = instructions

    # Load the instructions
    try:
        instruction_content = load_instruction(instruction_file)
    except Exception as e:
        print(f"Failed to load instructions: {str(e)}")
        instruction_content = "Generate a Discord server template with categories and channels."

    messages = [
        {"role": "system", "content": instruction_content},
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
            max_tokens=8000,
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
            return await gen_server(history, instruction_file)

        return "An error occurred while generating the server template. Please try again later."
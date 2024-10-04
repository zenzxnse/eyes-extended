import asyncio
from groq import AsyncGroq
from Global import config

async def analyze_image(image_data=None):
    if image_data is None:
        return {}
    
    client = AsyncGroq(api_key=config['API_KEYS']['API_KEY_7'])
    try:
        completion = await client.chat.completions.create(
            model="llama-3.2-11b-vision-preview",
            messages=[
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "text",
                            "text": "Provide a vivid description of this image. If there's any text in the image, explicitly state 'The image contains text: \"[exact text here]\"'. Then describe the visual elements, context, and any notable details."
                        },
                        {
                            "type": "image_url",
                            "image_url": {
                                "url": image_data
                            }
                        }
                    ]
                }
            ],
            temperature=0.7,
            max_tokens=8000,
            top_p=1,
            stream=False,
            stop=None,
        )
        print(completion.choices[0].message)
        return completion.choices[0].message
    except Exception as e:
        print(f"Image analysis failed: {e}")
        return {}
import os

def load_instruction(file_path):
    """Load instructions from a text file."""
    default_instructions = "You are a 目付き(Eyes) a discord bot, you are working in a confidential environment, keep your responses short and concise, and don't mention your name or mention the user unless it is necessary. only answer relevant questions, and don't make up new information. if you don't know the answer, say so, and don't make up new information. Make sure your answers are within 100 characters only exceeeding 100 characters when absolutely required."
    try:
        with open(file_path, 'r', encoding='utf-8') as file:
            instructions = file.read().strip()
        return instructions
    except Exception as e:
        print(f"Failed to load instructions: {e}")
        return default_instructions
    
if __name__ == "__main__":
    print(load_instruction("Augmentations/Ai/basic_instructions.txt"))
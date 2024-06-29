import yaml

def load_config(file_path = "Global_Configurations.yml", encoding = "utf-8") -> dict:
    with open(file_path, 'r', encoding=encoding) as file:
        return yaml.safe_load(file)
    
config = load_config()


import os
from dotenv import load_dotenv
from pymongo import MongoClient
from Global import config


load_dotenv()

# Create a new client and connect to the server
mongo_connection = config['MONGODB_CONNECTION']
uri = mongo_connection
mongo = MongoClient(uri)
from dotenv import load_dotenv
import os


load_dotenv()
DATABASE_NAME = os.getenv('DATABASE_NAME')
MODEL_NAME = os.getenv('MODEL_NAME')

import os
from dotenv import load_dotenv
load_dotenv()

class Settings:
    APP_NAME = 'Elite Futsal Performance'
    ENVIRONMENT = os.getenv('ENVIRONMENT', 'development')
    DATABASE_URL = os.getenv('DATABASE_URL', '')
    SECRET_KEY = os.getenv('SECRET_KEY', '')

settings = Settings()

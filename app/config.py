import os
from dotenv import load_dotenv

load_dotenv()


class Settings:

    APP_NAME = os.getenv(
        "APP_NAME",
        "Elite Futsal Performance"
    )

    DATABASE_URL = os.getenv(
        "DATABASE_URL"
    )

    SECRET_KEY = os.getenv(
        "SECRET_KEY",
        "chave-temporaria"
    )

    ENVIRONMENT = os.getenv(
        "ENVIRONMENT",
        "development"
    )


settings = Settings()

from fastapi import FastAPI

from app.config import settings


app = FastAPI(
    title=settings.APP_NAME,
    version="1.0.0"
)


@app.get("/")
def home():

    return {
        "sistema": "Elite Futsal Performance",
        "status": "online",
        "versao": "1.0.0"
    }

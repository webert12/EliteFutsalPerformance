from fastapi import FastAPI
from app.routes import auth
from app.database import criar_tabelas


app = FastAPI(
    title="Elite Futsal Performance",
    version="1.0.0"
)


@app.on_event("startup")
def iniciar():

    criar_tabelas()


@app.get("/")
def inicio():

    return {
        "sistema": "Elite Futsal Performance",
        "status": "online",
        "modulo": "Banco de dados iniciado"
    }

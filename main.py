from app.routes import auth
from fastapi import FastAPI

from app.database import criar_tabelas
from app.routes import auth


app = FastAPI(
    title="Elite Futsal Performance",
    version="1.0.0"
)


@app.on_event("startup")
def iniciar():

    criar_tabelas()


# Rotas do sistema
app.include_router(
    auth.router
)


@app.get("/")
def inicio():

    return {
        "sistema": "Elite Futsal Performance",
        "status": "online",
        "modulo": "Autenticação iniciado"
    }

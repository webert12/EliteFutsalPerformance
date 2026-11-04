from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.responses import HTMLResponse
from sqlalchemy import text
from app.config import settings
from app.database import Base, engine
from app import models  # register all SQLAlchemy models
from app.routes import auth, atletas, orientacoes

if not settings.SECRET_KEY or len(settings.SECRET_KEY) < 32:
    raise RuntimeError('Configure SECRET_KEY com pelo menos 32 caracteres no Render')

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Initial bootstrap only. Use Alembic migrations for schema changes in production.
    Base.metadata.create_all(bind=engine)
    yield

app = FastAPI(title=settings.APP_NAME, version='0.2.0', lifespan=lifespan)
from app.routes import administracao, treinos, rotina, acesso
app.include_router(administracao.router)
app.include_router(treinos.router)
app.include_router(rotina.router)
app.include_router(acesso.router)
app.include_router(auth.router)
app.include_router(atletas.router)
app.include_router(orientacoes.router)

@app.get('/api/status', response_class=HTMLResponse)
def inicio():
    return """<!doctype html><html lang="pt-BR"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>Elite Futsal Performance</title><style>body{margin:0;font-family:system-ui;background:#0b1220;color:#f1f5f9}main{max-width:760px;margin:8vh auto;padding:30px}h1{font-size:clamp(2rem,6vw,3.5rem)}p{line-height:1.6;color:#cbd5e1}.tag{color:#5eead4}a{display:inline-block;margin:10px 12px 0 0;padding:13px 18px;border-radius:10px;background:#0d9488;color:white;text-decoration:none}a.secondary{background:#334155}</style></head><body><main><p class="tag">⚽ FUTSAL DE BASE • PLATAFORMA EM DESENVOLVIMENTO</p><h1>Elite Futsal Performance</h1><p>Organização de atletas, registros de sono, hidratação, esforço e orientações educativas. Acesse a documentação interativa para testar cadastro e login.</p><a href="/docs">Abrir API / Testar sistema</a><a class="secondary" href="/health">Status do servidor</a><p>Os dados dos atletas são protegidos por autenticação. Planos individuais serão adicionados com revisão profissional.</p></main></body></html>"""

@app.get('/health')
def health():
    with engine.connect() as connection:
        connection.execute(text('SELECT 1'))
    return {'status': 'online', 'database': 'ok', 'versao': '0.2.0'}

# Interface web Elite Futsal Performance
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

app.mount("/static", StaticFiles(directory="web"), name="web")

@app.get("/", include_in_schema=False)
def pagina_inicial():
    return FileResponse("web/index.html")

@app.get("/responsavel", include_in_schema=False)
def pagina_responsavel():
    return FileResponse("web/responsavel.html")

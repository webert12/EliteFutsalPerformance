from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, sessionmaker
from app.config import settings

class Base(DeclarativeBase):
    pass

if not settings.DATABASE_URL:
    raise RuntimeError('DATABASE_URL ausente: configure no Render > Environment')

url = settings.DATABASE_URL
if url.startswith('postgres://'):
    url = 'postgresql://' + url[len('postgres://'):]

engine = create_engine(url, pool_pre_ping=True, pool_recycle=1800)
SessionLocal = sessionmaker(bind=engine, autoflush=False, expire_on_commit=False)

def get_db():
    with SessionLocal() as db:
        yield db

# Run once in a secure terminal. Do not expose as an endpoint.
import os
from app.database import Base, engine, SessionLocal
from app import models
from app.models.usuario import Usuario
from app.security.password import criar_hash_senha

email = os.getenv('ADMIN_EMAIL','').lower().strip()
senha = os.getenv('ADMIN_PASSWORD','')
nome = os.getenv('ADMIN_NAME','Administrador').strip()
if not email or len(senha) < 12:
    raise SystemExit('Configure ADMIN_EMAIL e ADMIN_PASSWORD (12+ caracteres) temporariamente')
Base.metadata.create_all(bind=engine)
with SessionLocal() as db:
    if db.query(Usuario).filter(Usuario.email == email).first():
        raise SystemExit('E-mail já cadastrado. Nenhuma permissão foi alterada.')
    db.add(Usuario(nome=nome, email=email, senha_hash=criar_hash_senha(senha), tipo_usuario='administrador'))
    db.commit()
print('Administrador criado. Remova ADMIN_PASSWORD do ambiente.')

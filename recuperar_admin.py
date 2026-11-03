import os
from app.database import SessionLocal
from app.models.usuario import Usuario
from app.security.password import criar_hash_senha

email = os.environ.get("ADMIN_EMAIL", "").strip().lower()
senha = os.environ.get("ADMIN_PASSWORD", "")

if not email or len(senha) < 12:
    raise SystemExit("Configure ADMIN_EMAIL e ADMIN_PASSWORD com 12+ caracteres")

with SessionLocal() as db:
    usuario = db.query(Usuario).filter(Usuario.email == email).first()

    if usuario is None:
        raise SystemExit(
            "Conta não encontrada neste banco. Nenhuma alteração realizada."
        )

    if usuario.tipo_usuario != "administrador":
        raise SystemExit(
            "Conta não é administradora. Nenhuma permissão alterada."
        )

    usuario.senha_hash = criar_hash_senha(senha)
    usuario.ativo = True
    db.commit()

print("Senha do administrador atualizada com sucesso.")

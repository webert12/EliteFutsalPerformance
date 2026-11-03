from datetime import datetime, timedelta, timezone
import jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.orm import Session
from app.config import settings
from app.database import get_db
from app.models.usuario import Usuario

bearer = HTTPBearer(auto_error=False)

def criar_token(usuario: Usuario):
    return jwt.encode({'sub': str(usuario.id), 'exp': datetime.now(timezone.utc)+timedelta(hours=8)}, settings.SECRET_KEY, algorithm='HS256')

def usuario_atual(credentials: HTTPAuthorizationCredentials | None = Depends(bearer), db: Session = Depends(get_db)) -> Usuario:
    erro = HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail='Autenticação necessária', headers={'WWW-Authenticate':'Bearer'})
    if not credentials:
        raise erro
    try:
        payload = jwt.decode(credentials.credentials, settings.SECRET_KEY, algorithms=['HS256'])
        uid = int(payload['sub'])
    except (jwt.InvalidTokenError, KeyError, ValueError, TypeError):
        raise erro
    usuario = db.get(Usuario, uid)
    if not usuario or not usuario.ativo:
        raise erro
    return usuario

def exigir_equipe(usuario: Usuario = Depends(usuario_atual)) -> Usuario:
    if usuario.tipo_usuario not in ('administrador','treinador'):
        raise HTTPException(status_code=403, detail='Acesso reservado à equipe')
    return usuario

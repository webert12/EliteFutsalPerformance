from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
from app.database import get_db
from app.models.usuario import Usuario
from app.schemas.usuario import UsuarioCriacao, UsuarioLogin, UsuarioPublico
from app.security.password import criar_hash_senha, verificar_senha
from app.security.token import criar_token, usuario_atual

router = APIRouter(prefix='/auth', tags=['Autenticação'])

@router.post('/cadastro', response_model=UsuarioPublico, status_code=201)
def cadastro(dados: UsuarioCriacao, db: Session = Depends(get_db)):
    # Public registration NEVER grants staff roles.
    email = str(dados.email).lower().strip()
    if db.query(Usuario).filter(Usuario.email == email).first():
        raise HTTPException(status_code=409, detail='Não foi possível cadastrar este e-mail')
    usuario = Usuario(nome=dados.nome.strip(), email=email, senha_hash=criar_hash_senha(dados.senha), tipo_usuario='atleta')
    db.add(usuario)
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(status_code=409, detail='Não foi possível cadastrar este e-mail')
    db.refresh(usuario)
    return usuario

@router.post('/login')
def login(dados: UsuarioLogin, db: Session = Depends(get_db)):
    usuario = db.query(Usuario).filter(Usuario.email == str(dados.email).lower().strip()).first()
    if not usuario or not verificar_senha(dados.senha, usuario.senha_hash) or not usuario.ativo:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail='Credenciais inválidas')
    return {'access_token': criar_token(usuario), 'token_type': 'bearer', 'tipo_usuario': usuario.tipo_usuario}

@router.get('/me', response_model=UsuarioPublico)
def me(usuario: Usuario = Depends(usuario_atual)):
    return usuario

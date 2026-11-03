"""Ações administrativas autenticadas. Nunca expor criação de equipe publicamente."""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
from app.database import get_db
from app.models.usuario import Usuario
from app.models.atleta import Atleta
from app.schemas.usuario import UsuarioCriacao, UsuarioPublico
from app.security.password import criar_hash_senha
from app.security.token import usuario_atual

router = APIRouter(prefix='/api/admin', tags=['Administração'])

def exigir_admin(usuario: Usuario = Depends(usuario_atual)) -> Usuario:
    if usuario.tipo_usuario != 'administrador':
        raise HTTPException(status_code=403, detail='Somente administradores')
    return usuario

@router.post('/treinadores', response_model=UsuarioPublico, status_code=201)
def criar_treinador(dados: UsuarioCriacao, admin: Usuario = Depends(exigir_admin), db: Session = Depends(get_db)):
    email = str(dados.email).strip().lower()
    if db.query(Usuario).filter(Usuario.email == email).first():
        raise HTTPException(status_code=409, detail='E-mail já cadastrado')
    usuario = Usuario(nome=dados.nome.strip(), email=email, senha_hash=criar_hash_senha(dados.senha), tipo_usuario='treinador')
    db.add(usuario)
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(status_code=409, detail='E-mail já cadastrado')
    db.refresh(usuario)
    return usuario

@router.get('/treinadores', response_model=list[UsuarioPublico])
def listar_treinadores(admin: Usuario = Depends(exigir_admin), db: Session = Depends(get_db)):
    return db.query(Usuario).filter(Usuario.tipo_usuario == 'treinador').order_by(Usuario.nome).all()

@router.get('/usuarios-atletas', response_model=list[UsuarioPublico])
def usuarios_sem_ficha(admin: Usuario = Depends(exigir_admin), db: Session = Depends(get_db)):
    return (db.query(Usuario).outerjoin(Atleta, Atleta.usuario_id == Usuario.id)
            .filter(Usuario.tipo_usuario == 'atleta', Usuario.ativo.is_(True), Atleta.id.is_(None))
            .order_by(Usuario.nome).all())

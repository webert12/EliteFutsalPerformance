from datetime import date
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
from app.database import get_db
from app.models.usuario import Usuario
from app.models.atleta import Atleta, RegistroDiario
from app.models.treino import Equipe, VinculoEquipe
from app.schemas.atleta import AtletaCriacao, AtletaPublico, RegistroCriacao, RegistroPublico
from app.security.token import usuario_atual, exigir_equipe

router = APIRouter(prefix='/api/atletas', tags=['Atletas'])

def autorizar(atleta: Atleta, usuario: Usuario):
    if usuario.tipo_usuario == 'treinador':
        # Check trainer-team membership in each endpoint using the request DB.
        raise HTTPException(status_code=403, detail='Use as rotas de equipes para acompanhar seus atletas')
    if usuario.tipo_usuario != 'administrador' and atleta.usuario_id != usuario.id:
        raise HTTPException(status_code=403, detail='Acesso não autorizado')

@router.post('', response_model=AtletaPublico, status_code=201)
def cadastrar(dados: AtletaCriacao, equipe: Usuario = Depends(exigir_equipe), db: Session = Depends(get_db)):
    if equipe.tipo_usuario != "administrador":
        raise HTTPException(status_code=403, detail="Somente administradores podem criar fichas")
    usuario = db.get(Usuario, dados.usuario_id)
    if not usuario or usuario.tipo_usuario != 'atleta':
        raise HTTPException(status_code=400, detail='Usuário atleta inválido')
    hoje = date.today()
    idade = hoje.year - dados.nascimento.year - ((hoje.month, hoje.day) < (dados.nascimento.month, dados.nascimento.day))
    if not 14 <= idade <= 17:
        raise HTTPException(status_code=422, detail='Esta versão atende atletas de 14 a 17 anos')
    atleta = Atleta(**dados.model_dump())
    db.add(atleta)
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(status_code=409, detail='Atleta já cadastrado ou dados duplicados')
    db.refresh(atleta)
    return atleta

@router.get('', response_model=list[AtletaPublico])
def listar(equipe: Usuario = Depends(exigir_equipe), db: Session = Depends(get_db)):
    if equipe.tipo_usuario == 'treinador':
        return (db.query(Atleta).join(VinculoEquipe, VinculoEquipe.atleta_id == Atleta.id)
                .join(Equipe, Equipe.id == VinculoEquipe.equipe_id)
                .filter(Equipe.treinador_id == equipe.id).distinct().order_by(Atleta.id).all())
    return db.query(Atleta).order_by(Atleta.id).all()

@router.get('/{atleta_id}', response_model=AtletaPublico)
def detalhe(atleta_id: int, usuario: Usuario = Depends(usuario_atual), db: Session = Depends(get_db)):
    atleta = db.get(Atleta, atleta_id)
    if not atleta:
        raise HTTPException(status_code=404, detail='Atleta não encontrado')
    autorizar(atleta, usuario)
    return atleta

@router.post('/{atleta_id}/registros', response_model=RegistroPublico, status_code=201)
def registrar(atleta_id: int, dados: RegistroCriacao, usuario: Usuario = Depends(usuario_atual), db: Session = Depends(get_db)):
    atleta = db.get(Atleta, atleta_id)
    if not atleta:
        raise HTTPException(status_code=404, detail='Atleta não encontrado')
    autorizar(atleta, usuario)
    if dados.dia > date.today():
        raise HTTPException(status_code=422, detail='Data futura não permitida')
    registro = RegistroDiario(atleta_id=atleta_id, **dados.model_dump())
    db.add(registro)
    db.commit()
    db.refresh(registro)
    return registro

@router.get('/{atleta_id}/registros', response_model=list[RegistroPublico])
def registros(atleta_id: int, usuario: Usuario = Depends(usuario_atual), db: Session = Depends(get_db)):
    atleta = db.get(Atleta, atleta_id)
    if not atleta:
        raise HTTPException(status_code=404, detail='Atleta não encontrado')
    autorizar(atleta, usuario)
    return db.query(RegistroDiario).filter(RegistroDiario.atleta_id == atleta_id).order_by(RegistroDiario.dia.desc(), RegistroDiario.id.desc()).limit(60).all()

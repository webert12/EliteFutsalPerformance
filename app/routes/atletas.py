from datetime import date
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
from app.database import get_db
from app.models.usuario import Usuario
from app.models.atleta import Atleta, RegistroDiario
from app.routes.acesso import exigir_consentimento
from app.models.acesso import Consentimento
from app.models.treino import Equipe, VinculoEquipe
from app.schemas.atleta import AtletaCriacao, AtletaPublico, RegistroCriacao, RegistroPublico
from app.security.token import usuario_atual, exigir_equipe

router = APIRouter(prefix='/api/atletas', tags=['Atletas'])

def autorizar(atleta: Atleta, usuario: Usuario):
    if usuario.tipo_usuario in ('treinador', 'administrador'):
        # Check trainer-team membership in each endpoint using the request DB.
        raise HTTPException(status_code=403, detail='Use as rotas de equipes para acompanhar seus atletas')
    if atleta.usuario_id != usuario.id:
        raise HTTPException(status_code=403, detail='Acesso não autorizado')

@router.post('', response_model=AtletaPublico, status_code=201)
def cadastrar(dados: AtletaCriacao, usuario: Usuario = Depends(usuario_atual), db: Session = Depends(get_db)):
    if usuario.tipo_usuario != 'atleta' or dados.usuario_id != usuario.id:
        raise HTTPException(403, 'A ficha deve ser cadastrada pelo próprio atleta')
    hoje = date.today()
    idade = hoje.year - dados.nascimento.year - ((hoje.month, hoje.day) < (dados.nascimento.month, dados.nascimento.day))
    if not 14 <= idade <= 17: raise HTTPException(422, 'Esta versão atende atletas de 14 a 17 anos')
    atleta = Atleta(**dados.model_dump(exclude={'observacoes'}))
    db.add(atleta)
    try: db.commit()
    except IntegrityError:
        db.rollback(); raise HTTPException(409, 'Ficha já cadastrada')
    db.refresh(atleta)
    return atleta

@router.get('/me', response_model=AtletaPublico)
def minha_ficha(usuario: Usuario = Depends(usuario_atual), db: Session = Depends(get_db)):
    if usuario.tipo_usuario != 'atleta': raise HTTPException(403, 'Somente atletas')
    atleta = db.query(Atleta).filter(Atleta.usuario_id == usuario.id).first()
    if not atleta: raise HTTPException(404, 'Preencha sua ficha esportiva')
    return atleta

@router.get('', response_model=list[AtletaPublico])
def listar(equipe: Usuario = Depends(exigir_equipe), db: Session = Depends(get_db)):
    if equipe.tipo_usuario == 'treinador':
        return (db.query(Atleta).join(VinculoEquipe, VinculoEquipe.atleta_id == Atleta.id)
                .join(Equipe, Equipe.id == VinculoEquipe.equipe_id)
                .join(Consentimento,Consentimento.atleta_id==Atleta.id)
                .filter(Equipe.treinador_id == equipe.id,Consentimento.aceito_em.is_not(None),Consentimento.revogado_em.is_(None)).distinct().order_by(Atleta.id).all())
    raise HTTPException(403, 'Acesso restrito aos treinadores')

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
    exigir_consentimento(db,atleta.id)
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
    exigir_consentimento(db,atleta.id)
    return db.query(RegistroDiario).filter(RegistroDiario.atleta_id == atleta_id).order_by(RegistroDiario.dia.desc(), RegistroDiario.id.desc()).limit(60).all()

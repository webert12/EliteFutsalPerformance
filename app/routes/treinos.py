from datetime import date
from pydantic import BaseModel, Field
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
from app.database import get_db
from app.models.usuario import Usuario
from app.models.atleta import Atleta
from app.models.treino import Equipe, VinculoEquipe, Treino, Presenca
from app.security.token import usuario_atual

router = APIRouter(prefix='/api/v4', tags=['Equipes e treinos'])

class EquipeNova(BaseModel):
    nome: str = Field(min_length=2, max_length=100)
    categoria: str = Field(pattern='^(sub-15|sub-17|outros)$')
    treinador_id: int
class VinculoNovo(BaseModel):
    atleta_id: int
class TreinoNovo(BaseModel):
    data: date
    objetivo: str = Field(min_length=3,max_length=240)
    duracao_min: int = Field(ge=1,le=240)
class PresencaNova(BaseModel):
    atleta_id: int
    situacao: str = Field(pattern='^(presente|ausente|justificado)$')

def admin(u):
    if u.tipo_usuario != 'administrador':
        raise HTTPException(403,'Somente administradores')
def acesso(equipe, u):
    if u.tipo_usuario != 'administrador' and not (u.tipo_usuario == 'treinador' and equipe.treinador_id == u.id):
        raise HTTPException(403,'Equipe não autorizada')
def obter_equipe(db,id,u):
    equipe=db.get(Equipe,id)
    if not equipe: raise HTTPException(404,'Equipe não encontrada')
    acesso(equipe,u)
    return equipe

def resumo_equipe(e):
    return {'id':e.id,'nome':e.nome,'categoria':e.categoria,'treinador_id':e.treinador_id}

@router.post('/equipes',status_code=201)
def criar_equipe(d:EquipeNova,u:Usuario=Depends(usuario_atual),db:Session=Depends(get_db)):
    admin(u)
    t=db.get(Usuario,d.treinador_id)
    if not t or not t.ativo or t.tipo_usuario!='treinador': raise HTTPException(422,'Treinador inválido')
    e=Equipe(**d.model_dump());db.add(e);db.commit();db.refresh(e)
    return resumo_equipe(e)

@router.get('/equipes')
def listar_equipes(u:Usuario=Depends(usuario_atual),db:Session=Depends(get_db)):
    if u.tipo_usuario not in ('administrador','treinador'): raise HTTPException(403,'Acesso restrito')
    q=db.query(Equipe)
    if u.tipo_usuario=='treinador':q=q.filter(Equipe.treinador_id==u.id)
    return [resumo_equipe(e) for e in q.order_by(Equipe.nome).all()]

@router.post('/equipes/{equipe_id}/atletas',status_code=201)
def vincular(equipe_id:int,d:VinculoNovo,u:Usuario=Depends(usuario_atual),db:Session=Depends(get_db)):
    admin(u);obter_equipe(db,equipe_id,u)
    if not db.get(Atleta,d.atleta_id):raise HTTPException(404,'Atleta não encontrado')
    v=VinculoEquipe(equipe_id=equipe_id,atleta_id=d.atleta_id);db.add(v)
    try:db.commit()
    except IntegrityError:db.rollback();raise HTTPException(409,'Atleta já vinculado à equipe')
    return {'equipe_id':equipe_id,'atleta_id':d.atleta_id}

@router.get('/equipes/{equipe_id}/atletas')
def atletas_equipe(equipe_id:int,u:Usuario=Depends(usuario_atual),db:Session=Depends(get_db)):
    obter_equipe(db,equipe_id,u)
    rows=db.query(Atleta,Usuario).join(VinculoEquipe,VinculoEquipe.atleta_id==Atleta.id).join(Usuario,Usuario.id==Atleta.usuario_id).filter(VinculoEquipe.equipe_id==equipe_id).order_by(Usuario.nome).all()
    return [{'id':a.id,'nome':p.nome,'posicao':a.posicao} for a,p in rows]

@router.post('/equipes/{equipe_id}/treinos',status_code=201)
def criar_treino(equipe_id:int,d:TreinoNovo,u:Usuario=Depends(usuario_atual),db:Session=Depends(get_db)):
    obter_equipe(db,equipe_id,u)
    if d.data>date.today():raise HTTPException(422,'Registre treinos realizados; datas futuras serão habilitadas no planejamento')
    t=Treino(equipe_id=equipe_id,**d.model_dump());db.add(t);db.commit();db.refresh(t)
    return {'id':t.id,'equipe_id':equipe_id,'data':t.data,'objetivo':t.objetivo,'duracao_min':t.duracao_min}

@router.get('/equipes/{equipe_id}/treinos')
def listar_treinos(equipe_id:int,u:Usuario=Depends(usuario_atual),db:Session=Depends(get_db)):
    obter_equipe(db,equipe_id,u)
    ts=db.query(Treino).filter(Treino.equipe_id==equipe_id).order_by(Treino.data.desc(),Treino.id.desc()).limit(50).all()
    return [{'id':t.id,'data':t.data,'objetivo':t.objetivo,'duracao_min':t.duracao_min} for t in ts]

@router.put('/treinos/{treino_id}/presencas')
def marcar(treino_id:int,d:PresencaNova,u:Usuario=Depends(usuario_atual),db:Session=Depends(get_db)):
    t=db.get(Treino,treino_id)
    if not t:raise HTTPException(404,'Treino não encontrado')
    obter_equipe(db,t.equipe_id,u)
    vinc=db.query(VinculoEquipe).filter_by(equipe_id=t.equipe_id,atleta_id=d.atleta_id).first()
    if not vinc:raise HTTPException(422,'Atleta não pertence à equipe')
    p=db.query(Presenca).filter_by(treino_id=treino_id,atleta_id=d.atleta_id).first()
    if p:p.situacao=d.situacao
    else:db.add(Presenca(treino_id=treino_id,**d.model_dump()))
    db.commit()
    return {'treino_id':treino_id,'atleta_id':d.atleta_id,'situacao':d.situacao}

@router.get('/treinos/{treino_id}/presencas')
def presencas(treino_id:int,u:Usuario=Depends(usuario_atual),db:Session=Depends(get_db)):
    t=db.get(Treino,treino_id)
    if not t:raise HTTPException(404,'Treino não encontrado')
    obter_equipe(db,t.equipe_id,u)
    return [{'atleta_id':p.atleta_id,'situacao':p.situacao} for p in db.query(Presenca).filter_by(treino_id=treino_id).all()]

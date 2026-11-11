"""V16 — partidas e estatísticas, sempre limitadas ao treinador proprietário e atletas autorizados."""
from datetime import date, timedelta
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session
from app.database import get_db
from app.models.usuario import Usuario
from app.models.treino import Equipe, VinculoEquipe
from app.models.jogos_v16 import JogoV16, EstatisticaV16
from app.routes.rotina import atleta_proprio
from app.routes.acesso import exigir_consentimento
from app.security.token import usuario_atual

router = APIRouter(prefix='/api/v16', tags=['V16 — Jogos e competições'])

class Partida(BaseModel):
    equipe_id: int
    dia: date
    adversario: str = Field(min_length=2,max_length=120)
    competicao: str = Field(min_length=2,max_length=120)
    local: str | None = Field(default=None,max_length=120)
    status: str = Field(pattern='^(agendado|finalizado)$')
    gols_pro: int = Field(default=0,ge=0,le=100)
    gols_contra: int = Field(default=0,ge=0,le=100)

class Estatistica(BaseModel):
    atleta_id: int
    gols: int = Field(ge=0,le=100)
    assistencias: int = Field(ge=0,le=100)
    minutos: int = Field(ge=0,le=120)

def equipe_autorizada(db,u,eid):
    if u.tipo_usuario != 'treinador': raise HTTPException(403,'Somente treinadores')
    e=db.get(Equipe,eid)
    if not e or e.treinador_id!=u.id:raise HTTPException(404,'Equipe não encontrada')
    return e

def jogo_autorizado(db,u,jid):
    if u.tipo_usuario != 'treinador':raise HTTPException(403,'Somente treinadores')
    j=db.get(JogoV16,jid)
    if not j or j.treinador_id!=u.id:raise HTTPException(404,'Jogo não encontrado')
    equipe_autorizada(db,u,j.equipe_id)
    return j

def publico(j):
    return {'id':j.id,'equipe_id':j.equipe_id,'dia':j.dia.isoformat(),'adversario':j.adversario,'competicao':j.competicao,'local':j.local,'status':j.status,'gols_pro':j.gols_pro if j.status=='finalizado' else None,'gols_contra':j.gols_contra if j.status=='finalizado' else None}

@router.post('/jogos',status_code=201)
def criar(d:Partida,u:Usuario=Depends(usuario_atual),db:Session=Depends(get_db)):
    equipe_autorizada(db,u,d.equipe_id)
    if not date.today()-timedelta(days=365)<=d.dia<=date.today()+timedelta(days=365):raise HTTPException(422,'Data fora do intervalo permitido')
    if d.status=='finalizado' and d.dia>date.today():raise HTTPException(422,'Jogo futuro não pode ser finalizado')
    j=JogoV16(treinador_id=u.id,**d.model_dump());db.add(j);db.commit();db.refresh(j)
    return publico(j)

@router.get('/equipes/{equipe_id}/jogos')
def listar(equipe_id:int,u:Usuario=Depends(usuario_atual),db:Session=Depends(get_db)):
    equipe_autorizada(db,u,equipe_id)
    return [publico(j) for j in db.query(JogoV16).filter_by(equipe_id=equipe_id,treinador_id=u.id).order_by(JogoV16.dia.desc(),JogoV16.id.desc()).limit(100).all()]

@router.put('/jogos/{jogo_id}')
def atualizar(jogo_id:int,d:Partida,u:Usuario=Depends(usuario_atual),db:Session=Depends(get_db)):
    j=jogo_autorizado(db,u,jogo_id)
    if j.equipe_id!=d.equipe_id:raise HTTPException(422,'Não é possível transferir jogo entre equipes')
    if d.status=='finalizado' and d.dia>date.today():raise HTTPException(422,'Jogo futuro não pode ser finalizado')
    for k,v in d.model_dump().items():setattr(j,k,v)
    db.commit();return publico(j)

@router.put('/jogos/{jogo_id}/atletas')
def estatistica(jogo_id:int,d:Estatistica,u:Usuario=Depends(usuario_atual),db:Session=Depends(get_db)):
    j=jogo_autorizado(db,u,jogo_id)
    if j.status!='finalizado':raise HTTPException(422,'Finalize o jogo antes de registrar estatísticas')
    if not db.query(VinculoEquipe).filter_by(equipe_id=j.equipe_id,atleta_id=d.atleta_id).first():raise HTTPException(403,'Atleta fora da equipe')
    exigir_consentimento(db,d.atleta_id)
    s=db.query(EstatisticaV16).filter_by(jogo_id=j.id,atleta_id=d.atleta_id).first()
    if not s:s=EstatisticaV16(jogo_id=j.id,atleta_id=d.atleta_id);db.add(s)
    for k in ('gols','assistencias','minutos'):setattr(s,k,getattr(d,k))
    db.commit()
    return {'jogo_id':j.id,**d.model_dump()}

@router.get('/jogos/{jogo_id}/atletas')
def estatisticas(jogo_id:int,u:Usuario=Depends(usuario_atual),db:Session=Depends(get_db)):
    j=jogo_autorizado(db,u,jogo_id)
    from app.models.acesso import Consentimento
    rows=db.query(EstatisticaV16).join(Consentimento,Consentimento.atleta_id==EstatisticaV16.atleta_id).filter(EstatisticaV16.jogo_id==j.id,Consentimento.aceito_em.is_not(None),Consentimento.revogado_em.is_(None)).all()
    return [{'atleta_id':s.atleta_id,'gols':s.gols,'assistencias':s.assistencias,'minutos':s.minutos} for s in rows]

@router.get('/meus-jogos')
def meus_jogos(u:Usuario=Depends(usuario_atual),db:Session=Depends(get_db)):
    a=atleta_proprio(db,u)
    ids=[eid for (eid,) in db.query(VinculoEquipe.equipe_id).filter_by(atleta_id=a.id).all()]
    if not ids:return []
    jogos=db.query(JogoV16).filter(JogoV16.equipe_id.in_(ids)).order_by(JogoV16.dia.desc()).limit(80).all()
    stats={s.jogo_id:s for s in db.query(EstatisticaV16).filter(EstatisticaV16.atleta_id==a.id,EstatisticaV16.jogo_id.in_([j.id for j in jogos])).all()}
    return [{**publico(j),'minhas_estatisticas':({'gols':stats[j.id].gols,'assistencias':stats[j.id].assistencias,'minutos':stats[j.id].minutos} if j.id in stats else None)} for j in jogos]

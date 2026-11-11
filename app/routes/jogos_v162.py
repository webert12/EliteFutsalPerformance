"""V16.2: escalação e estatísticas agregadas, com autorização por equipe."""
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session
from sqlalchemy import func
from app.database import get_db
from app.security.token import usuario_atual
from app.models.usuario import Usuario
from app.models.treino import VinculoEquipe
from app.models.jogos_v16 import JogoV16, EstatisticaV16
from app.models.jogos_v162 import EscalacaoV162
from app.routes.jogos_v16 import jogo_autorizado, equipe_autorizada
from app.routes.acesso import exigir_consentimento

router=APIRouter(prefix='/api/v162',tags=['V16.2 — Escalação e temporada'])
class EscalacaoEntrada(BaseModel):
    atleta_id:int
    titular:bool=False
    posicao:str=Field(default='linha',pattern='^(goleiro|fixo|ala|pivo|linha)$')
    amarelos:int=Field(default=0,ge=0,le=2)
    vermelho:bool=False

def serializar(e):
    return {'atleta_id':e.atleta_id,'titular':e.titular,'posicao':e.posicao,'amarelos':e.amarelos,'vermelho':e.vermelho}

@router.put('/jogos/{jogo_id}/escalacao')
def salvar(jogo_id:int,d:EscalacaoEntrada,u:Usuario=Depends(usuario_atual),db:Session=Depends(get_db)):
    j=jogo_autorizado(db,u,jogo_id)
    if not db.query(VinculoEquipe).filter_by(equipe_id=j.equipe_id,atleta_id=d.atleta_id).first():
        raise HTTPException(403,'Atleta não pertence à equipe')
    exigir_consentimento(db,d.atleta_id)
    e=db.query(EscalacaoV162).filter_by(jogo_id=j.id,atleta_id=d.atleta_id).first()
    if not e:
        e=EscalacaoV162(jogo_id=j.id,atleta_id=d.atleta_id);db.add(e)
    for key,value in d.model_dump().items():
        if key!='atleta_id':setattr(e,key,value)
    db.commit()
    return serializar(e)

@router.get('/jogos/{jogo_id}/escalacao')
def consultar(jogo_id:int,u:Usuario=Depends(usuario_atual),db:Session=Depends(get_db)):
    j=jogo_autorizado(db,u,jogo_id)
    from app.models.acesso import Consentimento
    rows=db.query(EscalacaoV162).join(Consentimento,Consentimento.atleta_id==EscalacaoV162.atleta_id).filter(EscalacaoV162.jogo_id==j.id,Consentimento.aceito_em.is_not(None),Consentimento.revogado_em.is_(None)).order_by(EscalacaoV162.titular.desc(),EscalacaoV162.atleta_id).all()
    return [serializar(e) for e in rows]

@router.get('/equipes/{equipe_id}/temporada')
def temporada(equipe_id:int,ano:int=2026,u:Usuario=Depends(usuario_atual),db:Session=Depends(get_db)):
    from datetime import date
    if ano<2020 or ano>date.today().year+1:raise HTTPException(422,'Ano inválido')
    equipe_autorizada(db,u,equipe_id)
    jogos=db.query(JogoV16).filter(JogoV16.equipe_id==equipe_id,JogoV16.treinador_id==u.id,JogoV16.dia>=date(ano,1,1),JogoV16.dia<=date(ano,12,31),JogoV16.status=='finalizado').all()
    ids=[j.id for j in jogos]
    v=e=d=gp=gc=0
    for j in jogos:
        gp+=j.gols_pro;gc+=j.gols_contra
        if j.gols_pro>j.gols_contra:v+=1
        elif j.gols_pro<j.gols_contra:d+=1
        else:e+=1
    from app.models.acesso import Consentimento
    atletas=[]
    if ids:
        rows=db.query(EstatisticaV16.atleta_id,func.sum(EstatisticaV16.gols),func.sum(EstatisticaV16.assistencias),func.sum(EstatisticaV16.minutos),func.count(EstatisticaV16.jogo_id)).join(Consentimento,Consentimento.atleta_id==EstatisticaV16.atleta_id).filter(EstatisticaV16.jogo_id.in_(ids),Consentimento.aceito_em.is_not(None),Consentimento.revogado_em.is_(None)).group_by(EstatisticaV16.atleta_id).all()
        atletas=[{'atleta_id':aid,'gols':int(g or 0),'assistencias':int(a or 0),'minutos':int(m or 0),'participacoes':int(p)} for aid,g,a,m,p in rows]
    return {'ano':ano,'jogos':len(jogos),'vitorias':v,'empates':e,'derrotas':d,'gols_pro':gp,'gols_contra':gc,'atletas':atletas}

from datetime import datetime, timezone
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
from app.database import get_db
from app.security.token import usuario_atual
from app.models.usuario import Usuario
from app.models.atleta import Atleta
from app.models.treino import Equipe, VinculoEquipe
from app.models.acesso import Consentimento
from app.models.comunicados_v17 import ComunicadoV17, CienciaV17

router=APIRouter(prefix='/api/v17',tags=['V17 Comunicados'])
class Novo(BaseModel):
    equipe_id:int=Field(gt=0)
    titulo:str=Field(min_length=3,max_length=120)
    mensagem:str=Field(min_length=5,max_length=2000)

def equipe_propria(db,u,eid):
    e=db.get(Equipe,eid)
    if u.tipo_usuario!='treinador' or not e or e.treinador_id!=u.id: raise HTTPException(403,'Equipe não autorizada')
    return e

def autorizado(db,aid,eid):
    return bool(db.query(VinculoEquipe).join(Consentimento,Consentimento.atleta_id==VinculoEquipe.atleta_id).filter(VinculoEquipe.atleta_id==aid,VinculoEquipe.equipe_id==eid,Consentimento.aceito_em.is_not(None),Consentimento.revogado_em.is_(None)).first())

@router.post('/comunicados',status_code=201)
def criar(d:Novo,u:Usuario=Depends(usuario_atual),db:Session=Depends(get_db)):
    equipe_propria(db,u,d.equipe_id)
    c=ComunicadoV17(equipe_id=d.equipe_id,treinador_id=u.id,titulo=d.titulo.strip(),mensagem=d.mensagem.strip())
    db.add(c);db.commit();db.refresh(c)
    return {'id':c.id,'titulo':c.titulo}

@router.get('/treinador')
def listar_treinador(equipe_id:int,u:Usuario=Depends(usuario_atual),db:Session=Depends(get_db)):
    equipe_propria(db,u,equipe_id)
    cs=db.query(ComunicadoV17).filter_by(equipe_id=equipe_id,treinador_id=u.id).order_by(ComunicadoV17.id.desc()).limit(50).all()
    return [{'id':c.id,'titulo':c.titulo,'mensagem':c.mensagem,'criado_em':c.criado_em.isoformat(),'ciencias':db.query(CienciaV17).filter_by(comunicado_id=c.id).count()} for c in cs]

@router.get('/meus-comunicados')
def meus(u:Usuario=Depends(usuario_atual),db:Session=Depends(get_db)):
    if u.tipo_usuario!='atleta':raise HTTPException(403,'Somente atletas')
    a=db.query(Atleta).filter_by(usuario_id=u.id).first()
    if not a:return []
    cs=(db.query(ComunicadoV17).join(VinculoEquipe,VinculoEquipe.equipe_id==ComunicadoV17.equipe_id).join(Consentimento,Consentimento.atleta_id==VinculoEquipe.atleta_id).filter(VinculoEquipe.atleta_id==a.id,Consentimento.aceito_em.is_not(None),Consentimento.revogado_em.is_(None)).order_by(ComunicadoV17.id.desc()).limit(60).all())
    ids=[c.id for c in cs]
    lidos={x.comunicado_id for x in db.query(CienciaV17).filter(CienciaV17.atleta_id==a.id,CienciaV17.comunicado_id.in_(ids)).all()} if ids else set()
    return [{'id':c.id,'titulo':c.titulo,'mensagem':c.mensagem,'criado_em':c.criado_em.isoformat(),'lido':c.id in lidos} for c in cs]

@router.post('/comunicados/{cid}/ciencia')
def ciencia(cid:int,u:Usuario=Depends(usuario_atual),db:Session=Depends(get_db)):
    if u.tipo_usuario!='atleta':raise HTTPException(403,'Somente atletas')
    a=db.query(Atleta).filter_by(usuario_id=u.id).first()
    c=db.get(ComunicadoV17,cid)
    if not a or not c or not autorizado(db,a.id,c.equipe_id):raise HTTPException(404,'Comunicado não encontrado')
    if not db.query(CienciaV17).filter_by(comunicado_id=cid,atleta_id=a.id).first():
        db.add(CienciaV17(comunicado_id=cid,atleta_id=a.id))
        try:db.commit()
        except IntegrityError:db.rollback()
    return {'lido':True}

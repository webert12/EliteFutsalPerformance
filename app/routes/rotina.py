from datetime import date, datetime, timezone, timedelta
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session
from app.database import get_db
from app.models.usuario import Usuario
from app.models.atleta import Atleta, RegistroDiario
from app.models.treino import Equipe, VinculoEquipe
from app.models.rotina import Tarefa
from app.routes.acesso import exigir_consentimento
from app.schemas.atleta import RegistroCriacao, RegistroPublico
from app.security.token import usuario_atual

router = APIRouter(prefix='/api/v5', tags=['Rotina individual'])

class TarefaNova(BaseModel):
    atleta_id: int
    dia: date
    titulo: str = Field(min_length=3, max_length=120)
    descricao: str = Field(min_length=3, max_length=800)

class Conclusao(BaseModel):
    concluida: bool

def atleta_proprio(db, usuario):
    if usuario.tipo_usuario != 'atleta': raise HTTPException(403, 'Somente atletas')
    a = db.query(Atleta).filter(Atleta.usuario_id == usuario.id).first()
    if not a: raise HTTPException(404, 'Cadastre sua ficha esportiva primeiro')
    exigir_consentimento(db,a.id)
    return a

def verificar_treinador(db, usuario, atleta_id):
    if usuario.tipo_usuario != 'treinador': raise HTTPException(403, 'Somente treinadores')
    vinculo = (db.query(VinculoEquipe).join(Equipe, Equipe.id == VinculoEquipe.equipe_id)
        .filter(Equipe.treinador_id == usuario.id, VinculoEquipe.atleta_id == atleta_id).first())
    if not vinculo: raise HTTPException(403, 'Atleta não vinculado a uma de suas equipes')
    exigir_consentimento(db,atleta_id)


def tarefa_json(t):
    return {'id':t.id, 'atleta_id':t.atleta_id, 'dia':t.dia, 'titulo':t.titulo,
            'descricao':t.descricao, 'concluida':bool(t.concluida_em)}

@router.post('/tarefas', status_code=201)
def criar_tarefa(d:TarefaNova, u:Usuario=Depends(usuario_atual), db:Session=Depends(get_db)):
    verificar_treinador(db,u,d.atleta_id)
    if not db.get(Atleta,d.atleta_id): raise HTTPException(404,'Atleta inexistente')
    if d.dia < date.today()-timedelta(days=7) or d.dia > date.today()+timedelta(days=90):
        raise HTTPException(422,'Escolha uma data entre os últimos 7 e os próximos 90 dias')
    t=Tarefa(treinador_id=u.id,**d.model_dump());db.add(t);db.commit();db.refresh(t)
    return tarefa_json(t)

@router.get('/minhas-tarefas')
def minhas_tarefas(u:Usuario=Depends(usuario_atual), db:Session=Depends(get_db)):
    a=atleta_proprio(db,u)
    ts=(db.query(Tarefa).filter(Tarefa.atleta_id==a.id,Tarefa.dia>=date.today()-timedelta(days=14),Tarefa.dia<=date.today()+timedelta(days=30))
        .order_by(Tarefa.dia,Tarefa.id).limit(150).all())
    return [tarefa_json(t) for t in ts]

@router.put('/minhas-tarefas/{tarefa_id}')
def concluir(tarefa_id:int,d:Conclusao,u:Usuario=Depends(usuario_atual),db:Session=Depends(get_db)):
    a=atleta_proprio(db,u);t=db.get(Tarefa,tarefa_id)
    if not t or t.atleta_id != a.id:raise HTTPException(404,'Tarefa não encontrada')
    t.concluida_em=datetime.now(timezone.utc) if d.concluida else None
    db.commit();return tarefa_json(t)

@router.get('/atletas/{atleta_id}/tarefas')
def tarefas_do_atleta(atleta_id:int,u:Usuario=Depends(usuario_atual),db:Session=Depends(get_db)):
    verificar_treinador(db,u,atleta_id)
    ts=db.query(Tarefa).filter(Tarefa.atleta_id==atleta_id).order_by(Tarefa.dia.desc(),Tarefa.id.desc()).limit(100).all()
    return [tarefa_json(t) for t in ts]

@router.post('/meu-registro',response_model=RegistroPublico,status_code=201)
def registrar_dia(d:RegistroCriacao,u:Usuario=Depends(usuario_atual),db:Session=Depends(get_db)):
    a=atleta_proprio(db,u)
    if d.dia>date.today() or d.dia<date.today()-timedelta(days=7):
        raise HTTPException(422,'Registro permitido para os últimos 7 dias')
    reg=db.query(RegistroDiario).filter_by(atleta_id=a.id,dia=d.dia).order_by(RegistroDiario.id.desc()).first()
    if reg:
        for k,v in d.model_dump().items():setattr(reg,k,v)
    else:
        reg=RegistroDiario(atleta_id=a.id,**d.model_dump());db.add(reg)
    db.commit();db.refresh(reg);return reg

@router.get('/meus-registros',response_model=list[RegistroPublico])
def meus_registros(u:Usuario=Depends(usuario_atual),db:Session=Depends(get_db)):
    a=atleta_proprio(db,u)
    return db.query(RegistroDiario).filter(RegistroDiario.atleta_id==a.id).order_by(RegistroDiario.dia.desc()).limit(30).all()

@router.get('/atletas/{atleta_id}/registros',response_model=list[RegistroPublico])
def registros_treinador(atleta_id:int,u:Usuario=Depends(usuario_atual),db:Session=Depends(get_db)):
    verificar_treinador(db,u,atleta_id)
    return db.query(RegistroDiario).filter(RegistroDiario.atleta_id==atleta_id).order_by(RegistroDiario.dia.desc()).limit(30).all()
